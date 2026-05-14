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

Пример обработки ошибки, возникающей при попытке открыть несуществующий файл. Для этого используется `error-chain`, библиотека, которая инкапсулирует большое количество шаблонного кода, необходимого для обработки ошибок в Rust.

`Io(std::io::Error)` внутри `foreign_links` автоматически преобразует структуру `std::io::Error` в тип, определенный макросом `error_chain!` и реализующий трейт `Error`.

В следующем примере мы пытаемся выяснить, сколько времени работает система путем открытия файла Unix `/proc/uptime` и разбора его содержимого для извлечения первого числа. Функция `read_uptime` возвращает время безотказной работы или ошибку.

```rust
use error_chain::error_chain;

use std::fs::File;
use std::io::Read;

error_chain!{
    foreign_links {
        Io(std::io::Error);
        ParseInt(std::num::ParseIntError);
    }
}

fn read_uptime() -> Result<u64> {
    let mut uptime = String::new();
    File::open("/proc/uptime")?.read_to_string(&mut uptime)?;

    Ok(uptime
        .split('.')
        .next()
        .ok_or("Невозможно разобрать данные")?
        .parse()?)
}

fn main() {
    match read_uptime() {
        Ok(uptime) => println!("Время безотказной работы: {} секунд", uptime),
        Err(err) => eprintln!("Ошибка: {}", err),
    };
}
```

## Обработка всех возможных ошибок

Крейт `error-chain` делает возможным и относительно компактным сопоставление разных типов ошибок, возвращаемых функцией. Тип ошибки определяется перечислением `ErrorKind`.

Используем `reqwest::blocking` для получения произвольного целого числа из веб-сервиса. Преобразуем строку из ответа в целое число. Стандартная библиотека Rust, `reqwest` и веб-сервис могут генерировать ошибки. Мы определяем ошибки с помощью `foreign_links`. Дополнительный вариант `ErrorKind` для веб-сервиса использует блок `errors` макроса `error_chain!`.

```rust
use error_chain::error_chain;

error_chain! {
    foreign_links {
        Io(std::io::Error);
        Reqwest(reqwest::Error);
        ParseIntError(std::num::ParseIntError);
    }
    errors { RandomResponseError(t: String) }
}

fn parse_response(response: reqwest::blocking::Response) -> Result<u32> {
    let mut body = response.text()?;
    body.pop();
    body.parse::<u32>()
        .chain_err(|| ErrorKind::RandomResponseError(body))
}

fn run() -> Result<()> {
    let url =
        format!("https://www.random.org/integers/?num=1&min=0&max=10&col=1&base=10&format=plain");
    let response = reqwest::blocking::get(&url)?;
    let random_value: u32 = parse_response(response)?;
    println!("Произвольное целое число между 0 и 10: {}", random_value);
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        match *error.kind() {
            ErrorKind::Io(_) => println!("Стандартная ошибка ввода/вывода: {:?}", error),
            ErrorKind::Reqwest(_) => println!("Ошибка Reqwest: {:?}", error),
            ErrorKind::ParseIntError(_) => {
                println!("Стандартная ошибка разбора целого числа: {:?}", error)
            }
            ErrorKind::RandomResponseError(_) => println!("Кастомная ошибка: {:?}", error),
            _ => println!("Другая ошибка: {:?}", error),
        }
    }
}
```

## Получение трассировки сложной ошибки

Следующий пример демонстрирует обработку сложной ошибки и вывод ее трассировки. `chain_err` используется для расширения списка возможных ошибок путем добавления новых ошибок. Стек ошибки может быть распутан (unwound), что предоставляет лучший контекст для понимания того, почему возникла ошибка.

В примере мы пытаемся десериализовать значение 256 в `u8`. Ошибка всплывает (bubble up) из `serde` через `csv` в пользовательский код.

```rust
use error_chain::error_chain;
use serde::Deserialize;

use std::fmt;

error_chain! {
    foreign_links {
        Reader(csv::Error);
    }
}

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
            .ok_or("Невозможно разобрать первую запись CSV")?
            .chain_err(|| "Невозможно разобрать цвет RGB")?;

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

    let rgb = Rgb::from_reader(csv.as_bytes()).chain_err(|| "Невозможно прочитать данные CSV")?;
    println!("{:?} в шестнадцатеричном формате: #{:X}", rgb, rgb);

    Ok(())
}

fn main() {
    if let Err(ref errors) = run() {
        eprintln!("Уровень ошибки - описание");
        errors
            .iter()
            .enumerate()
            .for_each(|(index, error)| eprintln!("└> {} - {}", index, error));

        if let Some(backtrace) = errors.backtrace() {
            eprintln!("{:?}", backtrace);
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
