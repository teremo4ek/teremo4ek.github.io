---
title: "Упражнения: Параллелизм"
description: "Практические задачи по многопоточности и параллелизму"
date: 2026-05-20T05:00:00Z
weight: 25
image: "/images/rust/25-uprazhneniya-parallellizm-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


Попрактикуемся применять новые знания на двух упражнениях:

- [обедающие философы](https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B4%D0%B0%D1%87%D0%B0_%D0%BE%D0%B1_%D0%BE%D0%B1%D0%B5%D0%B4%D0%B0%D1%8E%D1%89%D0%B8%D1%85_%D1%84%D0%B8%D0%BB%D0%BE%D1%81%D0%BE%D1%84%D0%B0%D1%85) - классическая задача параллелизма
- многопоточная проверка ссылок

__Обедающие философы__

Условия задачи:

Пять безмолвных философов сидят вокруг круглого стола, перед каждым философом стоит тарелка спагетти. На столе между каждой парой ближайших философов лежит по одной вилке.

Каждый философ может либо есть, либо размышлять. Прием пищи не ограничен количеством оставшихся спагетти - подразумевается бесконечный запас. Тем не менее, философ может есть только тогда, когда держит две вилки - взятую справа и слева.

Каждый философ может взять ближайшую вилку (если она доступна) или положить - если он уже держит ее. Взятие каждой вилки и возвращение ее на стол являются раздельными действиями, которые должны выполняться одно за другим.

Задача заключается в том, чтобы разработать модель (параллельный алгоритм), при которой ни один из философов не будет голодать, то есть будет чередовать прием пищи и размышления 100 раз.

```rust
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::Duration;

struct Fork;

struct Philosopher {
    name: String,
    // left_fork: ...
    // right_fork: ...
    // thoughts: ...
}

impl Philosopher {
    fn think(&self) {
        self.thoughts
            .send(format!("Эврика! {} сгенерировал(а) новую идею!", &self.name))
            .unwrap();
    }

    fn eat(&self) {
        // Берем вилки
        println!("{} ест...", &self.name);
        thread::sleep(Duration::from_millis(10));
    }
}

static PHILOSOPHERS: &[&str] =
    &["Сократ", "Гипатия", "Платон", "Аристотель", "Пифагор"];

fn main() {
    // Создаем вилки

    // Создаем философов

    // Каждый философ размышляет и ест 100 раз

    // Выводим размышления философов
}
```

Подсказка: рассмотрите возможность использования [std::mem::swap](https://doc.rust-lang.org/std/mem/fn.swap.html) для решения проблемы взаимной блокировки (deadlock).

<details>
<summary>Решение:</summary>

```rust
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::Duration;

struct Fork;

struct Philosopher {
    name: String,
    left_fork: Arc<Mutex<Fork>>,
    right_fork: Arc<Mutex<Fork>>,
    thoughts: mpsc::SyncSender<String>,
}

impl Philosopher {
    fn think(&self) {
        self.thoughts
            .send(format!("Эврика! {} сгенерировал(а) новую идею!", &self.name))
            .unwrap();
    }

    fn eat(&self) {
        println!("{} пытается есть", &self.name);

        let _left = self.left_fork.lock().unwrap();
        let _right = self.right_fork.lock().unwrap();

        println!("{} ест...", &self.name);

        thread::sleep(Duration::from_millis(10));
    }
}

static PHILOSOPHERS: &[&str] =
    &["Сократ", "Гипатия", "Платон", "Аристотель", "Пифагор"];

fn main() {
    let (tx, rx) = mpsc::sync_channel(10);

    let forks = (0..PHILOSOPHERS.len())
        .map(|_| Arc::new(Mutex::new(Fork)))
        .collect::<Vec<_>>();

    for i in 0..forks.len() {
        let tx = tx.clone();

        let mut left_fork = Arc::clone(&forks[i]);
        let mut right_fork = Arc::clone(&forks[(i + 1) % forks.len()]);

        // Во избежание взаимной блокировки нам необходимо где-то нарушить симметрию.
        // Меняем вилки местами без их повторной инициализации
        if i == forks.len() - 1 {
            std::mem::swap(&mut left_fork, &mut right_fork);
        }

        let philosopher = Philosopher {
            name: PHILOSOPHERS[i].to_string(),
            thoughts: tx,
            left_fork,
            right_fork,
        };

        thread::spawn(move || {
            for _ in 0..100 {
                philosopher.eat();
                philosopher.think();
            }
        });
    }

    drop(tx);

    for thought in rx {
        println!("{thought}");
    }
}
```

</details>

__Многопоточная проверка ссылок__

Создадим инструмент для многопоточной проверки ссылок. Он должен начинать с основной веб-страницы и проверять корректность ссылок на ней. Затем он должен рекурсивно проверять другие страницы в том же домене и продолжать делать это до тех пор, пока все страницы не будут проверены.

Для создания такого инструмента вам потребуется какой-нибудь клиент `HTTP`, например, [reqwest](https://docs.rs/reqwest/):

```bash
cargo add reqwest --features blocking,rustls-tls
```

Для обнаружения ссылок можно воспользоваться [scraper](https://docs.rs/scraper/):

```bash
cargo add scraper
```

Наконец, для обработки ошибок пригодится [thiserror](https://docs.rs/thiserror/):

```bash
cargo add thiserror
```

`Cargo.toml`:

```toml
[package]
name = "link-checker"
version = "0.1.0"
edition = "2021"
publish = false

[dependencies]
reqwest = { version = "0.11.12", features = ["blocking", "rustls-tls"] }
scraper = "0.13.0"
thiserror = "1.0.37"
```

Начните с небольшого сайта, такого как `https://www.google.org`.

`src/main.rs`:

```rust
use reqwest::blocking::Client;
use reqwest::Url;
use scraper::{Html, Selector};
use thiserror::Error;

#[derive(Error, Debug)]
enum Error {
    #[error("ошибка запроса: {0}")]
    ReqwestError(#[from] reqwest::Error),
    #[error("плохой ответ HTTP: {0}")]
    BadResponse(String),
}

#[derive(Debug)]
struct CrawlCommand {
    url: Url,
    extract_links: bool,
}

fn visit_page(client: &Client, command: &CrawlCommand) -> Result<Vec<Url>, Error> {
    println!("проверка {:#}", command.url);

    let response = client.get(command.url.clone()).send()?;

    if !response.status().is_success() {
        return Err(Error::BadResponse(response.status().to_string()));
    }

    let mut link_urls = Vec::new();

    if !command.extract_links {
        return Ok(link_urls);
    }

    let base_url = response.url().to_owned();
    let body_text = response.text()?;
    let document = Html::parse_document(&body_text);

    let selector = Selector::parse("a").unwrap();
    let href_values = document
        .select(&selector)
        .filter_map(|element| element.value().attr("href"));
    for href in href_values {
        match base_url.join(href) {
            Ok(link_url) => {
                link_urls.push(link_url);
            }
            Err(err) => {
                println!("в {base_url:#} не поддается разбору {href:?}: {err}");
            }
        }
    }
    Ok(link_urls)
}

fn main() {
    let client = Client::new();
    let start_url = Url::parse("https://www.google.org").unwrap();
    let crawl_command = CrawlCommand{ url: start_url, extract_links: true };

    match visit_page(&client, &crawl_command) {
        Ok(links) => println!("ссылки: {links:#?}"),
        Err(err) => println!("невозможно извлечь ссылки: {err:#}"),
    }
}
```

Задачи:

- используйте потоки для параллельной проверки ссылок: отправьте проверяемые URL-адреса в канал и позвольте нескольким потокам проверять URL-адреса параллельно
- реализуйте рекурсивное извлечение ссылок со всех страниц домена `www.google.org`. Установите верхний предел в 100 страниц или около того, чтобы сайт вас не заблокировал

<details>
<summary>Решение:</summary>

```rust
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::collections::HashSet;

use reqwest::blocking::Client;
use reqwest::Url;
use scraper::{Html, Selector};
use thiserror::Error;

#[derive(Error, Debug)]
enum Error {
    #[error("ошибка запроса: {0}")]
    ReqwestError(#[from] reqwest::Error),
    #[error("плохой ответ HTTP: {0}")]
    BadResponse(String),
}

#[derive(Debug)]
struct CrawlCommand {
    url: Url,
    extract_links: bool,
}

fn visit_page(client: &Client, command: &CrawlCommand) -> Result<Vec<Url>, Error> {
    println!("проверка {:#}", command.url);

    let response = client.get(command.url.clone()).send()?;

    if !response.status().is_success() {
        return Err(Error::BadResponse(response.status().to_string()));
    }

    let mut link_urls = Vec::new();

    if !command.extract_links {
        return Ok(link_urls);
    }

    let base_url = response.url().to_owned();
    let body_text = response.text()?;
    let document = Html::parse_document(&body_text);

    let selector = Selector::parse("a").unwrap();
    let href_values = document
        .select(&selector)
        .filter_map(|element| element.value().attr("href"));
    for href in href_values {
        match base_url.join(href) {
            Ok(link_url) => {
                link_urls.push(link_url);
            }
            Err(err) => {
                println!("в {base_url:#} не поддается разбору {href:?}: {err}");
            }
        }
    }
    Ok(link_urls)
}

struct CrawlState {
    domain: String,
    visited_pages: HashSet<String>,
}

impl CrawlState {
    fn new(start_url: &Url) -> CrawlState {
        let mut visited_pages = HashSet::new();

        visited_pages.insert(start_url.as_str().to_string());

        CrawlState {
            domain: start_url.domain().unwrap().to_string(),
            visited_pages
        }
    }

    /// Определяет, должны ли извлекаться ссылки на указанной странице
    fn should_extract_links(&self, url: &Url) -> bool {
        let Some(url_domain) = url.domain() else {
            return false;
        };
        url_domain == self.domain
    }

    /// Помечает указанную страницу как посещенную,
    /// возвращает `false`, если страница уже посещалась
    fn mark_visited(&mut self, url: &Url) -> bool {
        self.visited_pages.insert(url.as_str().to_string())
    }
}

type CrawlResult = Result<Vec<Url>, (Url, Error)>;

fn spawn_crawler_threads(
    command_receiver: mpsc::Receiver<CrawlCommand>,
    result_sender: mpsc::Sender<CrawlResult>,
    thread_count: u32,
) {
    let command_receiver = Arc::new(Mutex::new(command_receiver));

    for _ in 0..thread_count {
        let result_sender = result_sender.clone();
        let command_receiver = command_receiver.clone();

        thread::spawn(move || {
            let client = Client::new();

            loop {
                let command_result = {
                    let receiver_guard = command_receiver.lock().unwrap();
                    receiver_guard.recv()
                };

                let Ok(crawl_command) = command_result else {
                    // Отправитель уничтожен, команд больше не будет
                    break;
                };

                let crawl_result = match visit_page(&client, &crawl_command) {
                    Ok(link_urls) => Ok(link_urls),
                    Err(error) => Err((crawl_command.url, error)),
                };

                result_sender.send(crawl_result).unwrap();
            }
        });
    }
}

fn control_crawl(
    start_url: Url,
    command_sender: mpsc::Sender<CrawlCommand>,
    result_receiver: mpsc::Receiver<CrawlResult>,
) -> Vec<Url> {
    let mut crawl_state = CrawlState::new(&start_url);

    let start_command = CrawlCommand { url: start_url, extract_links: true };
    command_sender.send(start_command).unwrap();

    let mut pending_urls = 1;

    let mut bad_urls = Vec::new();

    while pending_urls > 0 {
        let crawl_result = result_receiver.recv().unwrap();
        pending_urls -= 1;

        match crawl_result {
            Ok(link_urls) => {
                for url in link_urls {
                    if crawl_state.mark_visited(&url) {
                        let extract_links = crawl_state.should_extract_links(&url);
                        let crawl_command = CrawlCommand { url, extract_links };
                        command_sender.send(crawl_command).unwrap();
                        pending_urls += 1;
                    }
                }
            }
            Err((url, error)) => {
                bad_urls.push(url);
                println!("при извлечении ссылок возникла ошибка: {:#}", error);
                continue;
            }
        }
    }
    bad_urls
}

fn check_links(start_url: Url) -> Vec<Url> {
    let (result_sender, result_receiver) = mpsc::channel::<CrawlResult>();
    let (command_sender, command_receiver) = mpsc::channel::<CrawlCommand>();
    spawn_crawler_threads(command_receiver, result_sender, 16);
    control_crawl(start_url, command_sender, result_receiver)
}

fn main() {
    let start_url = reqwest::Url::parse("https://www.google.org").unwrap();
    let bad_urls = check_links(start_url);
    println!("плохие URL: {:#?}", bad_urls);
}
```

</details>

# Асинхронный Rust

"Асинхронность" (async) - это модель параллелизма, в которой несколько задач выполняются одновременно. Каждая задача выполняется до тех пор, пока не завершится или не заблокируется, затем выполняется следующая (готовая к выполнению) задача и т.д. Такая модель позволяет выполнять большое количество задач с помощью небольшого числа потоков. Это связано с тем, что накладные расходы на выполнение каждой задачи обычно очень низкие, а операционные системы предоставляют примитивы для эффективного переключения между задачами.

Асинхронные операции `Rust` основаны на фьючерсах (futures, от "future" - будущее), представляющих собой работу, которая может быть завершена в будущем. Фьючерсы "опрашиваются" (polled) до тех пор, пока не сообщат о завершении.

Фьючерсы опрашиваются асинхронной средой выполнения (async runtime). Доступно несколько таких сред. Одной из самых популярных является [Tokio](https://tokio.rs/).

Сравнения:

- в `Python` используется похожая модель в `asyncio`. Однако, его тип `Future` основан на функциях обратного вызова (callbacks), а не на опросах. Асинхронные программы `Python` должны выполняться в цикле, как и асинхронные программы `Rust`
- `Promise` в `JavaScript` похож на фьючерс, но также основан на колбэках. Среды выполнения реализует цикл событий (event loop), поэтому многие детали разрешения промиса являются скрытыми
