---
title: "Кодирование"
description: "Наборы символов, обработка CSV и структурированные данные (JSON, TOML)"
date: 2026-05-14T05:00:00Z
weight: 9
image: "/images/image-placeholder.png"
categories: ["Rust"]
tags: ["rust", "кодирование"]
---

## Наборы символов

### Процентное кодирование строки

Пример процентного кодирования строки с помощью функции `utf8_percent_encode` из крейта `percent-encoding`. Декодирование строки выполняется с помощью функции `percent_decode`.

```rust
use percent_encoding::{utf8_percent_encode, percent_decode, AsciiSet, CONTROLS};
use std::str::Utf8Error;

const FRAGMENT: &AsciiSet = &CONTROLS.add(b' ').add(b'"').add(b'<').add(b'>').add(b'`');

fn main() -> Result<(), Utf8Error> {
    let input = "confident, productive systems programming";

    let iter = utf8_percent_encode(input, FRAGMENT);
    let encoded: String = iter.collect();
    assert_eq!(encoded, "confident,%20productive%20systems%20programming");

    let iter = percent_decode(encoded.as_bytes());
    let decoded = iter.decode_utf8()?;
    assert_eq!(decoded, "confident, productive systems programming");

    Ok(())
}
```

Набор кодировок (`FRAGMENT`) определяет, какие байты (помимо байтов, отличных от ASCII, и элементов управления (controls)) должны кодироваться. Состав этого набора зависит от контекста.

### Кодирование строки в application/x-www-form-urlencoded

Пример кодирования строки в `application/x-www-form-urlencoded` с помощью метода `form_urlencoded::byte_serialize`. Декодирование выполняется с помощью метода `form_urlencoded::parse`.

```rust
use url::form_urlencoded::{byte_serialize, parse};

fn main() {
    let urlencoded: String = byte_serialize("What is ❤?".as_bytes()).collect();
    assert_eq!(urlencoded, "What+is+%E2%9D%A4%3F");

    let decoded: String = parse(urlencoded.as_bytes())
        .map(|(key, val)| [key, val].concat())
        .collect();
    assert_eq!(decoded, "What is ❤?");
}
```

### Шестнадцатеричное кодирование и декодирование

Крейт `data_encoding` предоставляет метод `HEXUPPER::encode`, который принимает `&[u8]` и возвращает `String`, содержащую шестнадцатеричное представление данных. Этот крейт также предоставляет метод `HEXUPPER::decode`, который принимает `&[u8]` и возвращает `Vec<u8>` при успешном декодировании данных.

```rust
use data_encoding::{DecodeError, HEXUPPER};

fn main() -> Result<(), DecodeError> {
    let original = b"The quick brown fox jumps over the lazy dog.";
    let expected = "54686520717569636B2062726F776E20666F78206A756D7073206F76\
        57220746865206C617A7920646F672E";

    let encoded = HEXUPPER.encode(original);
    assert_eq!(encoded, expected);

    let decoded = HEXUPPER.decode(&encoded.into_bytes())?;
    assert_eq!(decoded, original);

    Ok(())
}
```

### base64 кодирование и декодирование

Крейт `base64` предоставляет методы `encode` и `decode` для кодирования и декодирования байтовых срезов в base64:

```rust
use error_chain::error_chain;

use base64::{engine::general_purpose::STANDARD, Engine as _};
use std::str;

error_chain! {
    foreign_links {
        Base64(base64::DecodeError);
        Utf8Error(str::Utf8Error);
    }
}

fn main() -> Result<()> {
    let hello = b"hello rustaceans";
    let encoded = STANDARD.encode(hello);
    let decoded = STANDARD.decode(&encoded)?;

    println!("origin: {}", str::from_utf8(hello)?);
    println!("base64 encoded: {}", encoded);
    println!("back to origin: {}", str::from_utf8(&decoded)?);

    Ok(())
}
```

## Обработка CSV

### Чтение записей CSV

Пример чтения стандартных записей CSV в структуру `csv::StringRecord` — слаботипизированное представление данных, которое ожидает валидные строки UTF-8. В качестве альтернативы можно использовать структуру `ByteRecord`, которая не проверяет строки.

```rust
use csv::Error;

fn main() -> Result<(), Error> {
    let csv = "year,make,model,description
1948,Porsche,356,Luxury sports car
1967,Ford,Mustang fastback 1967,American car";

    let mut reader = csv::Reader::from_reader(csv.as_bytes());
    for record in reader.records() {
        let record = record?;
        println!(
            "In {}, {} built the {} model. It is a {}.",
            &record[0], &record[1], &record[2], &record[3]
        );
    }

    Ok(())
}
```

Метод `csv::Reader::deserialize` десериализует данные в строготипизированные структуры. Обратите внимание на явную типизацию десериализуемой записи.

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct Record {
    year: u16,
    make: String,
    model: String,
    description: String,
}

fn main() -> Result<(), csv::Error> {
    let csv = "year,make,model,description
1948,Porsche,356,Luxury sports car
1967,Ford,Mustang fastback 1967,American car";

    let mut reader = csv::Reader::from_reader(csv.as_bytes());

    for record in reader.deserialize() {
        let record: Record = record?;
        println!(
            "In {}, {} built the {} model. It is a {}.",
            record.year,
            record.make,
            record.model,
            record.description
        );
    }

    Ok(())
}
```

### Чтение записей CSV с другим разделителем

Пример чтения записей CSV, разделителем которых является таб:

```rust
use csv::Error;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Record {
    name: String,
    place: String,
    #[serde(deserialize_with = "csv::invalid_option")]
    id: Option<u64>,
}

use csv::ReaderBuilder;

fn main() -> Result<(), Error> {
    let data = "name\tplace\tid
Mark\tMelbourne\t46
Ashley\tZurich\t92";

    let mut reader = ReaderBuilder::new()
        .delimiter(b'\t')
        .from_reader(data.as_bytes());
    for result in reader.deserialize::<Record>() {
        println!("{:?}", result?);
    }

    Ok(())
}
```

### Фильтрация записей CSV, совпадающих с предикатом

В следующем примере возвращаются только те строки `data`, которые совпадают с `query`:

```rust
use error_chain::error_chain;

use std::io;

error_chain! {
    foreign_links {
        Io(std::io::Error);
        CsvError(csv::Error);
    }
}

fn main() -> Result<()> {
    let query = "CA";
    let data = "\
City,State,Population,Latitude,Longitude
Kenai,AK,7610,60.5544444,-151.2583333
Oakman,AL,,33.7133333,-87.3886111
Sandfort,AL,,32.3380556,-85.2233333
West Hollywood,CA,37031,34.0900000,-118.3608333";

    let mut rdr = csv::ReaderBuilder::new().from_reader(data.as_bytes());
    let mut wtr = csv::Writer::from_writer(io::stdout());

    wtr.write_record(rdr.headers()?)?;

    for result in rdr.records() {
        let record = result?;
        if record.iter().any(|field| field == query) {
            wtr.write_record(&record)?;
        }
    }

    wtr.flush()?;
    Ok(())
}
```

### Обработка невалидных данных с помощью serde

Файлы CSV часто содержат невалидные данные. Для таких случаев крейт `csv` предоставляет кастомный десериализатор, `csv::invalid_option`, который автоматически преобразует невалидные данные в значения `None`:

```rust
use csv::Error;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Record {
    name: String,
    place: String,
    #[serde(deserialize_with = "csv::invalid_option")]
    id: Option<u64>,
}

fn main() -> Result<(), Error> {
    let data = "name,place,id
mark,sydney,46.5
ashley,zurich,92
akshat,delhi,37
alisha,colombo,xyz";

    let mut rdr = csv::Reader::from_reader(data.as_bytes());
    for result in rdr.deserialize() {
        let record: Record = result?;
        println!("{:?}", record);
    }

    Ok(())
}
```

### Сериализация записей в CSV

Пример сериализации кортежей Rust. Структура `csv::Writer` поддерживает автоматическую сериализацию типов Rust в записи CSV. Поскольку в средстве записи (writer) используется внутренний буфер, необходимо явно вызывать метод `flush` для его очистки.

```rust
use error_chain::error_chain;

use std::io;

error_chain! {
    foreign_links {
        CSVError(csv::Error);
        IOError(std::io::Error);
   }
}

fn main() -> Result<()> {
    let mut wtr = csv::Writer::from_writer(io::stdout());

    wtr.write_record(&["Name", "Place", "ID"])?;

    wtr.serialize(("Mark", "Sydney", 87))?;
    wtr.serialize(("Ashley", "Dublin", 32))?;
    wtr.serialize(("Akshat", "Delhi", 11))?;

    wtr.flush()?;
    Ok(())
}
```

### Сериализация записей в CSV с помощью serde

Пример сериализации кастомной структуры в запись CSV с помощью крейта `serde`:

```rust
use error_chain::error_chain;
use serde::Serialize;
use std::io;

error_chain! {
   foreign_links {
       IOError(std::io::Error);
       CSVError(csv::Error);
   }
}

#[derive(Serialize)]
struct Record<'a> {
    name: &'a str,
    place: &'a str,
    id: u64,
}

fn main() -> Result<()> {
    let mut wtr = csv::Writer::from_writer(io::stdout());

    let rec1 = Record {
        name: "Mark",
        place: "Melbourne",
        id: 56,
    };
    let rec2 = Record {
        name: "Ashley",
        place: "Sydney",
        id: 64,
    };
    let rec3 = Record {
        name: "Akshat",
        place: "Delhi",
        id: 98,
    };

    wtr.serialize(rec1)?;
    wtr.serialize(rec2)?;
    wtr.serialize(rec3)?;

    wtr.flush()?;

    Ok(())
}
```

## Структурированные данные

### Сериализация и десериализация неструктурированного JSON

Крейт `serde_json` предоставляет функцию `from_str` для разбора `&str` в формате JSON. Неструктурированный JSON разбирается в универсальный тип `serde_json::Value`, который может представлять любой валидный JSON.

```rust
use serde_json::json;
use serde_json::{Value, Error};

fn main() -> Result<(), Error> {
    let j = r#"{
                 "userid": 103609,
                 "verified": true,
                 "access_privileges": [
                   "user",
                   "admin"
                 ]
               }"#;

    let parsed: Value = serde_json::from_str(j)?;

    let expected = json!({
        "userid": 103609,
        "verified": true,
        "access_privileges": [
            "user",
            "admin"
        ]
    });

    assert_eq!(parsed, expected);

    Ok(())
}
```

### Десериализация TOML

Пример разбора TOML в универсальное `toml::Value`, которое может представлять любые валидные данные в формате TOML:

```rust
use toml::{Value, de::Error};

fn main() -> Result<(), Error> {
    let toml_content = r#"
          [package]
          name = "your_package"
          version = "0.1.0"
          authors = ["You! <you@example.org>"]

          [dependencies]
          serde = "1.0"
          "#;

    let package_info: Value = toml::from_str(toml_content)?;

    assert_eq!(package_info["dependencies"]["serde"].as_str(), Some("1.0"));
    assert_eq!(package_info["package"]["name"].as_str(),
               Some("your_package"));

    Ok(())
}
```

Крейт `serde` позволяет разбирать TOML в кастомные структуры:

```rust
use serde::Deserialize;
use std::collections::HashMap;
use toml::de::Error;

#[derive(Deserialize)]
struct Config {
    package: Package,
    dependencies: HashMap<String, String>,
}

#[derive(Deserialize)]
struct Package {
    name: String,
    version: String,
    authors: Vec<String>,
}

fn main() -> Result<(), Error> {
    let toml_content = r#"
          [package]
          name = "your_package"
          version = "0.1.0"
          authors = ["You! <you@example.org>"]

          [dependencies]
          serde = "1.0"
          "#;

    let package_info: Config = toml::from_str(toml_content)?;

    assert_eq!(package_info.package.name, "your_package");
    assert_eq!(package_info.package.version, "0.1.0");
    assert_eq!(package_info.package.authors, vec!["You! <you@example.org>"]);
    assert_eq!(package_info.dependencies["serde"], "1.0");

    Ok(())
}
```
