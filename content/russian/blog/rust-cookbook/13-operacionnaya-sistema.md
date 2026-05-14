---
title: "Операционная система"
description: "Запуск внешних команд, конвейеры, перенаправление ввода/вывода и переменные среды"
date: 2026-05-14T05:00:00Z
weight: 13
image: "/images/image-placeholder.png"
categories: ["Rust"]
tags: ["rust", "ОС"]
---

## Внешняя команда

### Запуск внешней команды и обработка stdout

Запускаем `git log --oneline` как внешнюю `Command` и исследуем ее `Output` с помощью `Regex` для получения хеша и сообщений последних 5 коммитов:

```rust
use error_chain::error_chain;

use std::process::Command;
use regex::Regex;

error_chain!{
    foreign_links {
        Io(std::io::Error);
        Regex(regex::Error);
        Utf8(std::string::FromUtf8Error);
    }
}

#[derive(PartialEq, Default, Clone, Debug)]
struct Commit {
    hash: String,
    message: String,
}

fn main() -> Result<()> {
    let output = Command::new("git").arg("log").arg("--oneline").output()?;

    if !output.status.success() {
        error_chain::bail!("Выполнение команды завершилось кодом ошибки");
    }

    let pattern = Regex::new(r"(?x)
                               ([0-9a-fA-F]+) # хеш коммита
                               (.*)           # сообщение коммита")?;

    String::from_utf8(output.stdout)?
        .lines()
        .filter_map(|line| pattern.captures(line))
        .map(|cap| {
                 Commit {
                     hash: cap[1].to_string(),
                     message: cap[2].trim().to_string(),
                 }
             })
        .take(5)
        .for_each(|x| println!("{:?}", x));

    Ok(())
}
```

Эта программа должна выполняться в директории с инициализированным GIT, содержащим хотя бы один коммит.

### Запуск внешней команды, передача ей stdin и проверка кода ошибки

Запускаем интерпретатор python с помощью внешней `Command` и передаем ему инструкцию для выполнения. Затем разбираем `Output`.

```rust
use error_chain::error_chain;

use std::collections::HashSet;
use std::io::Write;
use std::process::{Command, Stdio};

error_chain!{
    errors { CmdError }
    foreign_links {
        Io(std::io::Error);
        Utf8(std::string::FromUtf8Error);
    }
}

fn main() -> Result<()> {
    let mut child = Command::new("python").stdin(Stdio::piped())
        .stderr(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()?;

    child.stdin
        .as_mut()
        .ok_or("stdin дочернего процесса не был перехвачен")?
        .write_all(b"import this; copyright(); credits(); exit()")?;

    let output = child.wait_with_output()?;

    if output.status.success() {
        let raw_output = String::from_utf8(output.stdout)?;
        let words = raw_output.split_whitespace()
            .map(|s| s.to_lowercase())
            .collect::<HashSet<_>>();
        println!("Найдено {} уникальных слов:", words.len());
        println!("{:#?}", words);
        Ok(())
    } else {
        let err = String::from_utf8(output.stderr)?;
        error_chain::bail!("Выполнение внешней команды провалилось:\n {}", err)
    }
}
```

Для успешного выполнения этой программы на вашей машине должен быть установлен Python.

### Запуск внешних команд в конвейере

Получаем список из 10 самых больших файлов и директорий, находящихся в текущей рабочей директории с помощью команды `du -ah . | sort -hr | head -n 10`, выполняемой программно. `Command` представляет процесс. Вывод (output) дочернего процесса перехватывается с помощью `Stdio::piped` между предком и ребенком.

```rust
use error_chain::error_chain;

use std::process::{Command, Stdio};

error_chain! {
    foreign_links {
        Io(std::io::Error);
        Utf8(std::string::FromUtf8Error);
    }
}

fn main() -> Result<()> {
    let directory = std::env::current_dir()?;
    let mut du_output_child = Command::new("du")
        .arg("-ah")
        .arg(&directory)
        .stdout(Stdio::piped())
        .spawn()?;

    if let Some(du_output) = du_output_child.stdout.take() {
        let mut sort_output_child = Command::new("sort")
            .arg("-hr")
            .stdin(du_output)
            .stdout(Stdio::piped())
            .spawn()?;

        du_output_child.wait()?;

        if let Some(sort_output) = sort_output_child.stdout.take() {
            let head_output_child = Command::new("head")
                .args(&["-n", "10"])
                .stdin(sort_output)
                .stdout(Stdio::piped())
                .spawn()?;

            let head_stdout = head_output_child.wait_with_output()?;

            sort_output_child.wait()?;

            println!(
                "10 самых больших файлов и директорий в '{}':\n{}",
                directory.display(),
                String::from_utf8(head_stdout.stdout).unwrap()
            );
        }
    }

    Ok(())
}
```

Эта программа предназначена для выполнения в системах Unix.

### Перенаправление stdout и stderr дочернего процесса в один файл

Создаем (spawn) дочерний процесс и перенаправляем stdout и stderr в один и тот же файл. `File::try_clone` ссылается на один обработчик для stdout и stderr. Это гарантирует, что оба дескриптора пишут с одной и той же позиции курсора.

```rust
use std::fs::File;
use std::io::Error;
use std::process::{Command, Stdio};

fn main() -> Result<(), Error> {
    let outputs = File::create("out.txt")?;
    let errors = outputs.try_clone()?;

    Command::new("ls")
        .args(&[".", "oops"])
        .stdout(Stdio::from(outputs))
        .stderr(Stdio::from(errors))
        .spawn()?
        .wait_with_output()?;

    Ok(())
}
```

Эта программа предназначена для выполнения в системах Unix.

### Непрерывная обработка входных данных дочернего процесса

В следующем примере мы создаем конвейер с помощью `Stdio::piped` и непрерывно (continuously) читаем stdout при обновлении `BufReader`. Выполнение этой программы эквивалентно выполнению команды `journalctl | grep usb`.

```rust
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader, Error, ErrorKind};

fn main() -> Result<(), Error> {
    let stdout = Command::new("journalctl")
        .stdout(Stdio::piped())
        .spawn()?
        .stdout
        .ok_or_else(|| Error::new(ErrorKind::Other, "Невозможно перехватить stdout"))?;

    let reader = BufReader::new(stdout);

    reader
        .lines()
        .filter_map(|line| line.ok())
        .filter(|line| line.find("usb").is_some())
        .for_each(|line| println!("{}", line));

     Ok(())
}
```

Эта программа предназначена для выполнения в системах Unix.

### Чтение переменных среды окружения

Пример чтения переменной среды окружения с помощью `std::env::var`:

```rust
use std::env;
use std::fs;
use std::io::Error;

fn main() -> Result<(), Error> {
    let config_path = env::var("CONFIG")
        .unwrap_or("/etc/myapp/config".to_string());

    let config: String = fs::read_to_string(config_path)?;
    println!("Настройки: {}", config);

    Ok(())
}
```

Для чтения переменных из файлов `.env*` используется крейт `dotenv`.
