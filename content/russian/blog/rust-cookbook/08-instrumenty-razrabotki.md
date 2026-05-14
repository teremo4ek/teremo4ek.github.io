---
title: "Инструменты для разработки"
description: "Отладка с помощью логирования и версионирование с помощью semver"
date: 2026-05-14T05:00:00Z
weight: 8
image: "/images/rust-cookbook/08-instrumenty-razrabotki-cover.png"
categories: ["Rust"]
tags: ["rust", "инструменты"]
---

## Отладка

### Вывод сообщения об отладке в консоль

Крейт `log` предоставляет разные утилиты логирования. Крейт `env_logger` позволяет настраивать логирование через переменные среды окружения. Макрос `log::debug!` работает аналогично `std::fmt`.

```rust
fn execute_query(query: &str) {
    log::debug!("Выполнение запроса: {}", query);
}

fn main() {
    env_logger::init();
    execute_query("DROP TABLE students");
}
```

При запуске этого кода в консоль ничего не выводится, поскольку дефолтным уровнем логирования является `error`, а уровни ниже игнорируются. Для печати сообщений нужно установить переменную среды окружения `RUST_LOG` в значение `debug`:

```bash
RUST_LOG=debug cargo run
```

### Вывод сообщения об ошибке в консоль

Пример вывода в консоль сообщения об ошибке с помощью макроса `log::error!`:

```rust
fn execute_query(_query: &str) -> Result<(), &'static str> {
    Err("Боюсь, я не могу этого сделать")
}

fn main() {
    env_logger::init();

    let response = execute_query("DROP TABLE students");
    if let Err(err) = response {
        log::error!("Выполнить запрос не удалось: {}", err);
    }
}
```

### Вывод сообщения в stdout вместо stderr

Пример кастомной настройки логера с помощью `Builder::target` — установка цели вывода сообщения на `Target::Stdout`:

```rust
use env_logger::{Builder, Target};

fn main() {
    Builder::new()
        .target(Target::Stdout)
        .init();

    log::error!("Эта ошибка выводится в stdout");
}
```

### Вывод сообщения с помощью кастомного логера

Пример реализации кастомного логера `ConsoleLogger`, который выводит сообщения в stdout. `ConsoleLogger` реализует трейт `log::Log` для того, чтобы иметь возможность использовать макросы логирования. `log::set_logger` используется для установки `ConsoleLogger`.

```rust
use log::{Record, Level, Metadata, LevelFilter, SetLoggerError};

static CONSOLE_LOGGER: ConsoleLogger = ConsoleLogger;

struct ConsoleLogger;

impl log::Log for ConsoleLogger {
    fn enabled(&self, metadata: &Metadata) -> bool {
        metadata.level() <= Level::Info
    }

    fn log(&self, record: &Record) {
        if self.enabled(record.metadata()) {
            println!("Rust говорит: {} - {}", record.level(), record.args());
        }
    }

    fn flush(&self) {}
}

fn main() -> Result<(), SetLoggerError> {
    log::set_logger(&CONSOLE_LOGGER)?;
    log::set_max_level(LevelFilter::Info);

    log::info!("привет");
    log::warn!("предупреждение");
    log::error!("упс");
    Ok(())
}
```

### Определение уровня логирования для модуля

Создаем два модуля: `foo` и вложенный `foo::bar`. Определяем уровни логирования для каждого модуля через директивы логирования с помощью переменной среды окружения `RUST_LOG`.

```rust
mod foo {
    mod bar {
        pub fn run() {
            log::warn!("[bar] warn");
            log::info!("[bar] info");
            log::debug!("[bar] debug");
        }
    }

    pub fn run() {
        log::warn!("[foo] warn");
        log::info!("[foo] info");
        log::debug!("[foo] debug");
        bar::run();
    }
}

fn main() {
    env_logger::init();
    log::warn!("[root] warn");
    log::info!("[root] info");
    log::debug!("[root] debug");
    foo::run();
}
```

```bash
RUST_LOG="warn,test::foo=info,test::foo::bar=debug" ./test
```

Эта команда устанавливает дефолтный `log::level` в значение `warn`, уровни логирования в модулях `foo` и `foo::bar` в значения `info` и `debug`, соответственно.

### Использование кастомной переменной среды окружения для настройки логирования

Для настройки логирования используется структура `Builder`. Метод `Builder::parse` разбирает переменную среды окружения `MY_APP_LOG` в синтаксис `RUST_LOG`. Затем метод `Builder::init` инициализирует логер.

```rust
use std::env;
use env_logger::Builder;

fn main() {
    Builder::new()
        .parse(&env::var("MY_APP_LOG").unwrap_or_default())
        .init();

    log::info!("информация");
    log::warn!("предупреждение");
    log::error!("сообщение об {}", "ошибке");
}
```

### Добавление метки времени в сообщение об отладке

Создаем кастомную настройку логера с помощью `Builder`. Каждая сущность логирования вызывает `Local::now` для получения текущего `DateTime` в локальной временной зоне и использует `DateTime::format` с `strftime:specifiers` для формирования метки времени.

```rust
use std::io::Write;
use chrono::Local;
use env_logger::Builder;
use log::LevelFilter;

fn main() {
    Builder::new()
        .format(|buf, record| {
            writeln!(buf,
                "{} [{}] - {}",
                Local::now().format("%Y-%m-%dT%H:%M:%S"),
                record.level(),
                record.args()
            )
        })
        .filter(None, LevelFilter::Info)
        .init();

    log::warn!("warn");
    log::info!("info");
    log::debug!("debug");
}
```

## Версионирование

### Разбор и увеличение версии

Создаем структуру `semver::Version` из строкового литерала с помощью метода `Version::parse`, затем увеличиваем патчевый, минорный и мажорный номера версии один за другим.

```rust
use semver::{BuildMetadata, Error, Prerelease, Version};

fn main() -> Result<(), Error> {
    let parsed_version = Version::parse("0.2.6")?;

    assert_eq!(
        parsed_version,
        Version {
            major: 0,
            minor: 2,
            patch: 6,
            pre: Prerelease::EMPTY,
            build: BuildMetadata::EMPTY,
        }
    );

    Ok(())
}
```

### Разбор сложной версии

Создаем `semver::Version` из сложной строки с помощью `Version::parse`. Строка содержит номер предрелиза (pre-release) и метаданные о сборке (build metadata) согласно спецификации семантического версионирования.

```rust
use semver::{BuildMetadata, Error, Prerelease, Version};

fn main() -> Result<(), Error> {
    let version_str = "1.0.49-125+g72ee7853";
    let parsed_version = Version::parse(version_str)?;

    assert_eq!(
        parsed_version,
        Version {
            major: 1,
            minor: 0,
            patch: 49,
            pre: Prerelease::new("125").unwrap(),
            build: BuildMetadata::new("g72ee7853").unwrap()
        }
    );

    let serialized_version = parsed_version.to_string();
    assert_eq!(&serialized_version, version_str);

    Ok(())
}
```

### Поиск последней версии, входящей в диапазон

Имеется список версий, необходимо найти последнюю версию, удовлетворяющую условию. Структура `semver::VersionReq` фильтрует список с помощью метода `VersionReq::matches`.

```rust
use semver::{Error, Version, VersionReq};

fn find_max_matching_version<'a, I>(
    version_req_str: &str,
    iterable: I,
) -> Result<Option<Version>, Error>
where
    I: IntoIterator<Item = &'a str>,
{
    let vreq = VersionReq::parse(version_req_str)?;

    Ok(iterable
        .into_iter()
        .filter_map(|s| Version::parse(s).ok())
        .filter(|s| vreq.matches(s))
        .max())
}

fn main() -> Result<(), Error> {
    assert_eq!(
        find_max_matching_version("<= 1.0.0", vec!["0.9.0", "1.0.0", "1.0.1"])?,
        Some(Version::parse("1.0.0")?)
    );

    assert_eq!(
        find_max_matching_version(
            ">1.2.3-alpha.3",
            vec![
                "1.2.3-alpha.3",
                "1.2.3-alpha.4",
                "1.2.3-alpha.10",
                "1.2.3-beta.4",
                "3.4.5-alpha.9",
            ]
        )?,
        Some(Version::parse("1.2.3-beta.4")?)
    );

    Ok(())
}
```

### Проверка внешней версии команды на совместимость

Запускаем `git --version` с помощью структуры `Command`, затем разбираем номер версии в структуру `semver::Version` с помощью метода `Version::parse`. Метод `Version::matches` сравнивает структуру `semver:VersionReq` с разобранной версией.

```rust
use error_chain::error_chain;

use semver::{Version, VersionReq};
use std::process::Command;

error_chain! {
    foreign_links {
        Io(std::io::Error);
        Utf8(std::string::FromUtf8Error);
        SemVer(semver::Error);
    }
}

fn main() -> Result<()> {
    let version_constraint = ">=2.39.2";
    let version_test = VersionReq::parse(version_constraint)?;
    let output = Command::new("git").arg("--version").output()?;

    if !output.status.success() {
        error_chain::bail!("Выполнение команды завершилось ошибкой");
    }

    let stdout = String::from_utf8(output.stdout)?;
    let version = stdout
        .split(" ")
        .last()
        .ok_or_else(|| "Невалидный вывод команды")?;
    let version = version.split(".").take(3).collect::<Vec<_>>().join(".");
    let parsed_version = Version::parse(&version)?;

    if !version_test.matches(&parsed_version) {
        error_chain::bail!(
            "Версия команды ниже минимальной поддерживаемой версии (обнаружена {}, требуется {})",
            parsed_version,
            version_constraint
        );
    }

    Ok(())
}
```
