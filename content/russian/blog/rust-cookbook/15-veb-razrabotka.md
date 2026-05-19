---
title: "Веб-разработка"
description: "Извлечение ссылок, работа с URL, типы медиа и HTTP-клиенты"
date: 2026-05-14T05:00:00Z
weight: 15
image: "/images/rust-cookbook/15-veb-razrabotka-cover.png"
categories: ["Rust"]
tags: ["rust", "веб"]
---

## Извлечение ссылок

### Извлечение всех ссылок из HTML-страницы

Выполняем GET-запрос HTTP с помощью `reqwest::get` и разбираем ответ в документ HTML с помощью `Document::from_read`. `find` с `a` в `Name` извлекает все ссылки. Вызов `filter_map` на `Selection` извлекает URL из ссылок, имеющих `attr` (атрибут) `href`.

```rust
use error_chain::error_chain;
use select::document::Document;
use select::predicate::Name;

error_chain! {
      foreign_links {
          ReqError(reqwest::Error);
          IoError(std::io::Error);
      }
}

#[tokio::main]
async fn main() -> Result<()> {
    let res = reqwest::get("https://www.rust-lang.org/en-US/")
        .await?
        .text()
        .await?;

    Document::from(res.as_str())
        .find(Name("a"))
        .filter_map(|n| n.attr("href"))
        .for_each(|x| println!("{}", x));

  Ok(())
}
```

### Поиск сломанных ссылок на веб-странице

Вызываем `get_base_url` для извлечения базового URL. Перебираем ссылки документа и создаем задачу с помощью `tokio::spawn` для разбора индивидуальной ссылки. Задача выполняет запрос с помощью `reqwest` и проверяет `StatusCode` ответа.

```rust
use error_chain::error_chain;
use reqwest::StatusCode;
use select::document::Document;
use select::predicate::Name;
use std::collections::HashSet;
use url::{Position, Url};

error_chain! {
  foreign_links {
      ReqError(reqwest::Error);
      IoError(std::io::Error);
      UrlParseError(url::ParseError);
      JoinError(tokio::task::JoinError);
  }
}

async fn get_base_url(url: &Url, doc: &Document) -> Result<Url> {
  let base_tag_href = doc.find(Name("base")).filter_map(|n| n.attr("href")).nth(0);
  let base_url =
    base_tag_href.map_or_else(|| Url::parse(&url[..Position::BeforePath]), Url::parse)?;
  Ok(base_url)
}

async fn check_link(url: &Url) -> Result<bool> {
  let res = reqwest::get(url.as_ref()).await?;
  Ok(res.status() != StatusCode::NOT_FOUND)
}

#[tokio::main]
async fn main() -> Result<()> {
  let url = Url::parse("https://www.rust-lang.org/en-US/")?;
  let res = reqwest::get(url.as_ref()).await?.text().await?;
  let document = Document::from(res.as_str());
  let base_url = get_base_url(&url, &document).await?;
  let base_parser = Url::options().base_url(Some(&base_url));
  let links: HashSet<Url> = document
    .find(Name("a"))
    .filter_map(|n| n.attr("href"))
    .filter_map(|link| base_parser.parse(link).ok())
    .collect();
    let mut tasks = vec![];

    for link in links {
        tasks.push(tokio::spawn(async move {
            if check_link(&link).await.unwrap() {
                println!("Ссылка `{}` в порядке", link);
            } else {
                println!("Ссылка `{}` сломана", link);
            }
        }));
    }

    for task in tasks {
        task.await?
    }

  Ok(())
}
```

### Извлечение уникальных ссылок из разметки MediaWiki

Получаем страницу MediaWiki с помощью `reqwest::get` и ищем все внутренние и внешние ссылки с помощью `Regex::captures_iter`. Использование `Cow` позволяет избежать чрезмерного выделения (allocation) `String`.

```rust
use lazy_static::lazy_static;
use regex::Regex;
use std::borrow::Cow;
use std::collections::HashSet;
use std::error::Error;

fn extract_links(content: &str) -> HashSet<Cow<str>> {
  lazy_static! {
    static ref WIKI_REGEX: Regex = Regex::new(
        r"(?x)
            \[\[(?P<internal>[^\[\]|]*)[^\[\]]*\]\]    # внутренние ссылки
            |
            (url=|URL\||\[)(?P<external>http.*?)[ \|}] # внешние ссылки
        "
    )
    .unwrap();
  }

  let links: HashSet<_> = WIKI_REGEX
    .captures_iter(content)
    .map(|c| match (c.name("internal"), c.name("external")) {
      (Some(val), None) => Cow::from(val.as_str().to_lowercase()),
      (None, Some(val)) => Cow::from(val.as_str()),
      _ => unreachable!(),
    })
    .collect();

  links
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
  let content = reqwest::get(
    "https://en.wikipedia.org/w/index.php?title=Rust_(programming_language)&action=raw",
  )
  .await?
  .text()
  .await?;

  println!("{:#?}", extract_links(content.as_str()));

  Ok(())
}
```

## URL

### Разбор URL из строки в тип Url

Метод `parse` крейта `url` валидирует и разбирает `&str` в структуру `Url`. Строка может быть повреждена, поэтому `parse` возвращает `Result<Url, ParseError>`.

```rust
use url::{Url, ParseError};

fn main() -> Result<(), ParseError> {
    let s = "https://github.com/rust-lang/rust/issues?labels=E-easy&state=open";

    let parsed = Url::parse(s)?;
    println!("Путь URL: {}", parsed.path());

    Ok(())
}
```

### Создание базового URL путем удаления сегментов пути

Базовый URL включает протокол и домен. Метод `PathSegmentsMut::clear` удаляет пути, а метод `Url::set_query` удаляет строку запроса.

```rust
use error_chain::error_chain;
use url::Url;

error_chain! {
    foreign_links {
        UrlParse(url::ParseError);
    }
    errors {
        CannotBeABase
    }
}

fn main() -> Result<()> {
    let full = "https://github.com/rust-lang/cargo?asdf";

    let url = Url::parse(full)?;
    let base = base_url(url)?;

    println!("Базовый URL: {}", base);

    Ok(())
}

fn base_url(mut url: Url) -> Result<Url> {
    match url.path_segments_mut() {
        Ok(mut path) => {
            path.clear();
        }
        Err(_) => {
            return Err(Error::from_kind(ErrorKind::CannotBeABase));
        }
    }

    url.set_query(None);

    Ok(url)
}
```

### Создание новых URL из базового

Метод `join` позволяет создавать новые URL из базового и относительного путей:

```rust
use url::{Url, ParseError};

fn main() -> Result<(), ParseError> {
    let path = "/rust-lang/cargo";

    let gh = build_github_url(path)?;

    println!("Объединенный URL: {}", gh);

    Ok(())
}

fn build_github_url(path: &str) -> Result<Url, ParseError> {
    const GITHUB: &'static str = "https://github.com";

    let base = Url::parse(GITHUB)?;
    let joined = base.join(path)?;

    Ok(joined)
}
```

### Извлечение источника (схема / хост / порт)

Структура `Url` предоставляет разные методы для извлечения информации об URL, который она представляет:

```rust
use url::{Url, Host, ParseError};

fn main() -> Result<(), ParseError> {
    let s = "ftp://rust-lang.org/examples";

    let url = Url::parse(s)?;

    assert_eq!(url.scheme(), "ftp");
    assert_eq!(url.host(), Some(Host::Domain("rust-lang.org")));
    assert_eq!(url.port_or_known_default(), Some(21));

    Ok(())
}
```

### Удаление идентификаторов фрагментов и пар запросов из URL

Разбираем строку в структуру `Url` и обрезаем URL с помощью `url::Position` для удаления лишних частей:

```rust
use url::{Url, Position, ParseError};

fn main() -> Result<(), ParseError> {
    let parsed = Url::parse("https://github.com/rust-lang/rust/issues?labels=E-easy&state=open")?;
    let cleaned: &str = &parsed[..Position::AfterPath];
    println!("Очищенный URL: {}", cleaned);
    Ok(())
}
```

## Типы медиа

### Извлечение MIME-типа из строки

Следующий пример демонстрирует разбор строки в тип MIME с помощью крейта `mime`. Структура `FromStrError` генерирует дефолтный MIME-тип в методе `unwrap_or`.

```rust
use mime::{Mime, APPLICATION_OCTET_STREAM};

fn main() {
    let invalid_mime_type = "i n v a l i d";
    let default_mime = invalid_mime_type
        .parse::<Mime>()
        .unwrap_or(APPLICATION_OCTET_STREAM);

    println!(
        "MIME для {:?} - дефолтный {:?}",
        invalid_mime_type, default_mime
    );

    let valid_mime_type = "TEXT/PLAIN";
    let parsed_mime = valid_mime_type
        .parse::<Mime>()
        .unwrap_or(APPLICATION_OCTET_STREAM);

    println!(
        "MIME для {:?} был разобран как {:?}",
        valid_mime_type, parsed_mime
    );
}
```

### Извлечение MIME-типа из названия файла

Программа проверяет расширение файла и ищет совпадение с известным списком. Возвращаемым значением является `mime::Mime`.

```rust
use mime::Mime;

fn find_mimetype (filename : &String) -> Mime {
    let parts : Vec<&str> = filename.split('.').collect();

    let res = match parts.last() {
            Some(v) =>
                match *v {
                    "png" => mime::IMAGE_PNG,
                    "jpg" => mime::IMAGE_JPEG,
                    "json" => mime::APPLICATION_JSON,
                    _ => mime::TEXT_PLAIN,
                },
            None => mime::TEXT_PLAIN,
        };

    return res;
}

fn main() {
    let filenames = vec!("foobar.jpg", "foo.bar", "foobar.png");
    for file in filenames {
        let mime = find_mimetype(&file.to_owned());
     	println!("MIME для {}: {}", file, mime);
     }
}
```

### Извлечение MIME-типа из ответа HTTP

При получении ответа HTTP с помощью `reqwest` MIME-тип можно найти в заголовке `Content-Type`. Крейт `mime` затем может разобрать эту строку в значение `mime::Mime`.

```rust
use error_chain::error_chain;
use mime::Mime;
use std::str::FromStr;
use reqwest::header::CONTENT_TYPE;

error_chain! {
    foreign_links {
        Reqwest(reqwest::Error);
        Header(reqwest::header::ToStrError);
        Mime(mime::FromStrError);
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let response = reqwest::get("https://www.rust-lang.org/logos/rust-logo-32x32.png").await?;
    let headers = response.headers();

    match headers.get(CONTENT_TYPE) {
        None => {
            println!("Ответ не содержит заголовка `Content-Type`");
        }
        Some(content_type) => {
            let content_type = Mime::from_str(content_type.to_str()?)?;
            let media_type = match (content_type.type_(), content_type.subtype()) {
                (mime::TEXT, mime::HTML) => "документ HTML",
                (mime::TEXT, _) => "текст",
                (mime::IMAGE, mime::PNG) => "изображение PNG",
                (mime::IMAGE, _) => "изображение",
                _ => "не текст и не изображение",
            };

            println!("Ответ содержит {}", media_type);
        }
    };

    Ok(())
}
```

## Клиенты

### Отправка запроса HTTP

Отправляем синхронный GET-запрос HTTP с помощью метода `reqwest::blocking::get`, получаем структуру `reqwest::blocking::Response`, читаем тело ответа в `String` с помощью метода `read_to_string`.

```rust
use error_chain::error_chain;
use std::io::Read;

error_chain! {
    foreign_links {
        Io(std::io::Error);
        HttpRequest(reqwest::Error);
    }
}

fn main() -> Result<()> {
    let mut res = reqwest::blocking::get("http://httpbin.org/get")?;
    let mut body = String::new();
    res.read_to_string(&mut body)?;

    println!("Статус: {}", res.status());
    println!("Заголовки:\n{:#?}", res.headers());
    println!("Тело ответа:\n{}", body);

    Ok(())
}
```

Асинхронный вариант с использованием крейта `tokio`:

```rust
use error_chain::error_chain;

error_chain! {
    foreign_links {
        Io(std::io::Error);
        HttpRequest(reqwest::Error);
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let res = reqwest::get("http://httpbin.org/get").await?;
    println!("Статус: {}", res.status());
    println!("Заголовки:\n{:#?}", res.headers());

    let body = res.text().await?;
    println!("Тело ответа:\n{}", body);
    Ok(())
}
```

### Обращение к GitHub API

Отправляем запрос к stargazers API v3 с помощью `reqwest::get` для получения списка пользователей, поставивших звезду проекту GitHub. Структура `reqwest::Response` десериализуется в структуру `User`, реализующую трейт `serde::Deserialize`.

```rust
use reqwest::{header::USER_AGENT, Error};
use serde::Deserialize;

#[derive(Deserialize, Debug)]
struct User {
    login: String,
    id: u32,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let request_url = format!(
        "https://api.github.com/repos/{owner}/{repo}/stargazers",
        owner = "harryheman",
        repo = "my-js"
    );
    println!("{}", request_url);

    let client = reqwest::Client::new();
    let response = client
        .get(request_url)
        .header(USER_AGENT, "")
        .send()
        .await?;

    let users: Vec<User> = response.json().await?;
    println!("{:?}", users);
    Ok(())
}
```

### Проверка существования ресурса API

Отправляем HEAD-запрос HTTP (`Client::head`) в конечную точку пользователей GitHub и определяем успех по статусу ответа. Настройка `reqwest::Client` с помощью метода `ClientBuilder::timeout` отменяет запрос, если он выполняется дольше 5 секунд.

```rust
use reqwest::header::USER_AGENT;
use reqwest::ClientBuilder;
use reqwest::Result;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    let user = "harryheman";
    let request_url = format!("https://api.github.com/users/{}", user);
    println!("{}", request_url);

    let timeout = Duration::new(5, 0);
    let client = ClientBuilder::new().timeout(timeout).build()?;
    let response = client
        .head(&request_url)
        .header(USER_AGENT, "")
        .send()
        .await?;

    if response.status().is_success() {
        println!("{} является пользователем", user);
    } else {
        println!("{} не является пользователем", user);
    }

    Ok(())
}
```

### Создание и удаление Gist с помощью GitHub API

Создаем gist с помощью POST-запроса HTTP (`Client::post`) к gists API v3 и удаляем его с помощью DELETE-запроса (`Client::delete`). Для авторизации в GitHub API необходимо создать токен доступа и добавить его в файл `.env`.

```rust
use dotenv::dotenv;
use error_chain::error_chain;
use reqwest::{
    header::{AUTHORIZATION, USER_AGENT},
    Client,
};
use serde::Deserialize;
use serde_json::json;
use std::env;

error_chain! {
    foreign_links {
        EnvVar(env::VarError);
        HttpRequest(reqwest::Error);
    }
}

#[derive(Deserialize, Debug)]
struct Gist {
    id: String,
    html_url: String,
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenv().ok();

    let gist_body = json!({
        "description": "описание gist",
        "public": true,
        "files": {
            "main.rs": {
            "content": r#"fn main() { println!("всем привет!");}"#
            }
    }});

    let request_url = "https://api.github.com/gists";
    let response = Client::new()
        .post(request_url)
        .header(USER_AGENT, "")
        .header(AUTHORIZATION, format!("Bearer {}", env::var("GH_TOKEN")?))
        .json(&gist_body)
        .send()
        .await?;

    if response.status().is_success() {
        let gist: Gist = response.json().await?;
        println!("Создан {:?}", gist);

        let request_url = format!("{}/{}", request_url, gist.id);
        let response = Client::new()
            .delete(&request_url)
            .header(USER_AGENT, "")
            .header(AUTHORIZATION, format!("Bearer {}", env::var("GH_TOKEN")?))
            .send()
            .await?;

        if response.status().is_success() {
            println!(
                "Gist {} удален. Статус-код: {}",
                gist.id,
                response.status()
            );
        } else {
            println!("Запрос провалился. Статус-код: {}", response.status());
        }
    } else {
        println!("Запрос провалился. Статус-код: {}", response.status());
    }

    Ok(())
}
```

### Скачивание файла во временную директорию

Создаем временную директорию с помощью структуры `tempfile::Builder` и асинхронно скачиваем в нее файл через HTTP с помощью метода `reqwest::get`. Временная директория автоматически удаляется после завершения программы.

```rust
use error_chain::error_chain;
use std::fs::File;
use std::io::copy;
use tempfile::Builder;

error_chain! {
     foreign_links {
         Io(std::io::Error);
         HttpRequest(reqwest::Error);
     }
}

#[tokio::main]
async fn main() -> Result<()> {
    let tmp_dir = Builder::new().prefix("example").tempdir()?;
    let target = "https://www.rust-lang.org/logos/rust-logo-512x512.png";
    let response = reqwest::get(target).await?;

    let mut dest = {
        let fname = response
            .url()
            .path_segments()
            .and_then(|segments| segments.last())
            .and_then(|name| if name.is_empty() { None } else { Some(name) })
            .unwrap_or("tmp.bin");
        println!("файл для скачивания: '{}'", fname);
        let fname = tmp_dir.path().join(fname);
        println!("будет находиться в: '{:?}'", fname);
        File::create(fname)?
    };
    let content = response.text().await?;
    copy(&mut content.as_bytes(), &mut dest)?;
    std::thread::sleep(std::time::Duration::from_secs(5));
    Ok(())
}
```

### Отправка файла в paste-rs

`reqwest::Client` устанавливает соединение с `https://paste.rs`. `Client::post` определяет назначение POST-запроса HTTP, `RequestBuilder::body` устанавливает тело запроса, а `RequestBuilder::send` отправляет запрос.

```rust
use error_chain::error_chain;
use std::fs::File;
use std::io::Read;

error_chain! {
    foreign_links {
        HttpRequest(reqwest::Error);
        IoError(::std::io::Error);
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let paste_api = "https://paste.rs";
    let mut file = File::open("message.txt")?;

    let mut contents = String::new();
    file.read_to_string(&mut contents)?;

    let client = reqwest::Client::new();
    let res = client.post(paste_api).body(contents).send().await?;
    let response_text = res.text().await?;
    println!("{}", response_text);
    Ok(())
}
```

### Частичная загрузка файла по HTTP с помощью заголовка диапазона

Используем `reqwest::blocking::Client::head` для получения `Content-Length` (размера содержимого) ответа. Используем `reqwest::blocking::Client::get` для загрузки содержимого по частям размером 10240 байт с отслеживанием прогресса.

```rust
use anyhow::{bail, Context, Result};
use reqwest::header::{HeaderValue, CONTENT_LENGTH, RANGE};
use reqwest::StatusCode;
use std::fs::{self, File};
use std::str::FromStr;

struct PartialRangeIter {
    start: u64,
    end: u64,
    buffer_size: u32,
}

impl PartialRangeIter {
    pub fn new(start: u64, end: u64, buffer_size: u32) -> Result<Self> {
        if buffer_size == 0 {
            bail!("invalid `buffer_size`, must be greater than 0");
        }
        Ok(PartialRangeIter {
            start,
            end,
            buffer_size,
        })
    }
}

impl Iterator for PartialRangeIter {
    type Item = HeaderValue;

    fn next(&mut self) -> Option<Self::Item> {
        if self.start > self.end {
            None
        } else {
            let prev_start = self.start;

            self.start += std::cmp::min(self.buffer_size as u64, self.end - self.start + 1);

            Some(
                HeaderValue::from_str(&format!("bytes={}-{}", prev_start, self.start - 1)).unwrap(),
            )
        }
    }
}

fn main() -> Result<()> {
    let url = "https://httpbin.org/range/102400?duration=2";
    const CHUNK_SIZE: u32 = 10000;

    let client = reqwest::blocking::Client::new();
    let response = client.head(url).send()?;
    let length = response
        .headers()
        .get(CONTENT_LENGTH)
        .context("response does not contain content length")?;
    let length = u64::from_str(length.to_str()?).context("invalid `Content-Length` header")?;

    fs::create_dir_all("output")?;
    let mut output_file = File::create("output/download.bin")?;

    println!("starting download...");
    for range in PartialRangeIter::new(0, length - 1, CHUNK_SIZE)? {
        println!("range {:?}", range);
        let mut response = client.get(url).header(RANGE, range).send()?;

        let status = response.status();
        if !(status == StatusCode::OK || status == StatusCode::PARTIAL_CONTENT) {
            bail!("unexpected server response: {}", status)
        }
        std::io::copy(&mut response, &mut output_file)?;
    }

    println!("download completed successfully");

    Ok(())
}
```

### Базовая аутентификация

Для выполнения базовой аутентификации HTTP используется метод `reqwest::RequestBuilder::basic_auth`:

```rust
use reqwest::blocking::Client;
use reqwest::Error;

fn main() -> Result<(), Error> {
    let client = Client::new();

    let user_name = "testuser".to_string();
    let password: Option<String> = None;

    let response = client
        .get("https://httpbin.org/")
        .basic_auth(user_name, password)
        .send()?;

    println!("{:?}", response);

    Ok(())
}
```
