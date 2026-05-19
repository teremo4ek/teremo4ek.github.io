---
title: "Обработка ошибок"
description: "Правильная обработка ошибок в main, работа со всеми типами ошибок и получение трассировок"
date: 2026-05-14T05:00:00Z
weight: 10
image: "/images/rust-cookbook/10-obrabotka-oshibok-cover.png"
categories: ["Rust"]
tags: ["rust", "обработка ошибок"]
---

## Правильная обработка ошибок в main

Пример обработки ошибки, возникающей при попытке открыть несуществующий файл. Для этого используется `anyhow`, библиотека, которая инкапсулирует большое количество шаблонного кода, необходимого для обработки ошибок в Rust.

```rust
use anyhow::{Context, Result};

use std::fs::File;
use std::io::Read;

fn read_uptime() -> Result<u64> {
    let mut uptime = String::new();
    File::open("/proc/uptime")?.read_to_string(&mut uptime)?;

    let first_part = uptime
        .split('.')
        .next()
        .ok_or_else(|| anyhow::anyhow!("Невозможно разобрать данные"))?;

    Ok(first_part.parse()?)
}

fn main() {
    match read_uptime().context("не удалось прочитать uptime") {
        Ok(uptime) => println!("Время безотказной работы: {} секунд", uptime),
        Err(err) => eprintln!("Ошибка: {:#}", err),
    };
}
```

## Обработка всех возможных ошибок

Используем `reqwest::blocking` для получения произвольного целого числа из веб-сервиса. Преобразуем строку из ответа в целое число. Стандартная библиотека Rust, `reqwest` и веб-сервис могут генерировать ошибки. .

```rust
use anyhow::{anyhow, Context, Result};

fn parse_response(response: reqwest::blocking::Response) -> Result<u32> {
    let mut body = response.text()?;
    body.pop();
    body.parse::<u32>()
        .with_context(|| anyhow!("Unexpected response: {}", body))
}

fn run() -> Result<()> {
    let url =
        format!("https://www.random.org/integers/?num=1&min=0&max=10&col=1&base=10&format=plain");
    let response = reqwest::blocking::get(&url)?;
    let random_value: u32 = parse_response(response)?;
    println!("Random integer between 0 and 10: {}", random_value);
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        if let Some(_err) = error.downcast_ref::<std::io::Error>() {
            println!("Standard I/O error: {:?}", error);
        } else if let Some(_err) = error.downcast_ref::<reqwest::Error>() {
            println!("Reqwest error: {:?}", error);
        } else if let Some(_err) = error.downcast_ref::<std::num::ParseIntError>() {
            println!("Parse int error: {:?}", error);
        } else {
            println!("Other error: {:?}", error);
        }
    }
}
```

## Получение трассировки сложной ошибки

Следующий пример демонстрирует обработку сложной ошибки и вывод ее трассировки. Для этого используется крейт `anyhow`.

В примере мы пытаемся десериализовать значение 256 в `u8`. Ошибка всплывает (bubble up) из `serde` через `csv` в пользовательский код.

```rust
use anyhow::{anyhow, Context, Result};
use serde::Deserialize;

use std::fmt;

#[derive(Debug, Deserialize)]
struct Rgb {
    red: u8,
    blue: u8,
    green: u8,
}

impl Rgb {
    fn from_reader(csv_data: &[u8]) -> Result<Rgb> {
        let color: Rgb = csv::Reader::from_reader(csv_data)
            .deserialize()
            .nth(0)
            .ok_or_else(|| anyhow!("Cannot parse first CSV record"))?
            .context("Cannot parse RGB color")?;

        Ok(color)
    }
}

impl fmt::UpperHex for Rgb {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let hexa = u32::from(self.red) << 16 | u32::from(self.blue) << 8 | u32::from(self.green);
        write!(f, "{:X}", hexa)
    }
}

fn run() -> Result<()> {
    let csv = "red,blue,green
102,256,204";

    let rgb = Rgb::from_reader(csv.as_bytes()).context("Cannot read CSV data")?;
    println!("{:?} in hexadecimal format: #{:X}", rgb, rgb);

    Ok(())
}

fn main() {
    if let Err(err) = run() {
        let chain = err.chain().enumerate().collect::<Vec<_>>();
        if chain.len() > 1 {
            eprintln!("Error chain:");
            chain.iter().for_each(|(i, e)| eprintln!("  {}> {}", i, e));
        } else {
            eprintln!("Error: {:#}", err);
        }
    }
}

```

Обратная трассировка ошибки:

```
Уровень ошибки - описание
└> 0 - Невозможно прочитать данные CSV
└> 1 - Невозможно разобрать цвет RGB
└> 2 - CSV deserialize error: record 1 (line: 2, byte: 15): field 1: number too large to fit in target type
```

Запустите пример с `RUST_BACKTRACE=1` для отображения подробной обратной трассировки этой ошибки.
