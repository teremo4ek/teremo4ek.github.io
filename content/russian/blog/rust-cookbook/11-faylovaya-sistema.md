---
title: "Файловая система"
description: "Чтение и запись файлов, обход директорий и поиск файлов"
date: 2026-05-14T05:00:00Z
weight: 11
image: "/images/rust-cookbook/11-faylovaya-sistema-cover.png"
categories: ["Rust"]
tags: ["rust", "файловая система"]
---

## Чтение и запись

### Чтение строк из файла

Записываем сообщение, состоящее из трех строк, в файл, затем читаем его построчно с помощью итератора `Lines`, созданного с помощью метода `BufRead::lines`. Структура `File` реализует трейт `Read`, который предоставляет трейт `BufReader`. Метод `File::create` открывает файл для записи, а метод `File::open` — для чтения.

```rust
use std::fs::File;
use std::io::{Write, BufReader, BufRead, Error};

fn main() -> Result<(), Error> {
    let path = "lines.txt";

    let mut output = File::create(path)?;
    write!(output, "Rust\n💖\nFun")?;

    let input = File::open(path)?;
    let buffered = BufReader::new(input);

    for line in buffered.lines() {
        println!("{}", line?);
    }

    Ok(())
}
```

### Блокировка одновременного чтения и записи файла

Структура `same_file::Handle` используется для сравнения обработчика файла с другими обработчиками. В следующем примере сравниваются обработчики чтения и записи файла:

```rust
use same_file::Handle;
use std::fs::File;
use std::io::{BufRead, BufReader, Error, ErrorKind};
use std::path::Path;

fn main() -> Result<(), Error> {
    let path_to_read = Path::new("message.txt");

    let stdout_handle = Handle::stdout()?;
    let handle = Handle::from_path(path_to_read)?;

    if stdout_handle == handle {
        return Err(Error::new(
            ErrorKind::Other,
            "Вы читаете и пишете в один и тот же файл",
        ));
    } else {
        let file = File::open(&path_to_read)?;
        let file = BufReader::new(file);
        for (num, line) in file.lines().enumerate() {
            println!("{} : {}", num, line?.to_uppercase());
        }
    }

    Ok(())
}
```

### Произвольный доступ к файлу с помощью карты памяти

Создаем карту памяти (memory map) с помощью `memmap` и имитируем произвольные чтения файла. Использование карты памяти означает, что мы индексируем фрагмент, а не пытаемся перемещаться по файлу.

```rust
use memmap::Mmap;
use std::fs::File;
use std::io::{Write, Error};

fn main() -> Result<(), Error> {
    write!(File::create("content.txt")?, "My hovercraft is full of eels!")?;

    let file = File::open("content.txt")?;
    let map = unsafe { Mmap::map(&file)? };

    let random_indexes = [0, 1, 2, 19, 22, 10, 11, 29];
    assert_eq!(&map[3..13], b"hovercraft");
    let random_bytes: Vec<u8> = random_indexes.iter()
        .map(|&idx| map[idx])
        .collect();
    assert_eq!(&random_bytes[..], b"My loaf!");
    Ok(())
}
```

## Обход директории

### Получение названий файлов, модифицированных в течение последних 24 часов

Получаем текущую рабочую директорию путем вызова `env::current_dir`, затем для каждой сущности в `fs::read_dir`, извлекаем `DirEntry::path` и получаем метаданные через `fs::Metadata`. `Metadata::modified` возвращает `SystemTime::elapsed` — время, прошедшее с момента последней модификации.

```rust
use error_chain::error_chain;

use std::{env, fs};

error_chain! {
    foreign_links {
        Io(std::io::Error);
        SystemTimeError(std::time::SystemTimeError);
    }
}

fn main() -> Result<()> {
    let current_dir = env::current_dir()?;
    println!(
        "Файлы, модифицированные в течение последних 24 часов в {:?}:",
        current_dir
    );

    for entry in fs::read_dir(current_dir)? {
        let entry = entry?;
        let path = entry.path();
        let metadata = fs::metadata(&path)?;
        let last_modified = metadata.modified()?.elapsed()?.as_secs();

        if last_modified < 24 * 3600 && metadata.is_file() {
            println!(
                "Файл: {:?}, с момента последней модификации прошло {:?} секунд, файл доступен только для чтения: {:?}, размер: {:?} байтов.",
                path.file_name().ok_or("Название файла отсутствует")?,
                last_modified,
                metadata.permissions().readonly(),
                metadata.len(),
            );
        }
    }

    Ok(())
}
```

### Рекурсивный поиск дубликатов

Пример рекурсивного поиска повторяющихся файлов, находящихся в текущей директории:

```rust
use std::collections::HashMap;
use walkdir::WalkDir;

fn main() {
    let mut filenames = HashMap::new();

    for entry in WalkDir::new(".")
            .into_iter()
            .filter_map(Result::ok)
            .filter(|e| !e.file_type().is_dir()) {
        let f_name = String::from(entry.file_name().to_string_lossy());
        let counter = filenames.entry(f_name.clone()).or_insert(0);
        *counter += 1;
        if *counter == 2 {
            println!("{}", f_name);
        }
    }
}
```

### Рекурсивный поиск файлов с заданным предикатом

Пример поиска всех файлов JSON, находящихся в текущей директории и модифицированных в течение последних 24 часов. Метод `follow_links` считает символические ссылки обычными директориями и файлами.

```rust
use error_chain::error_chain;

use walkdir::WalkDir;

error_chain! {
    foreign_links {
        WalkDir(walkdir::Error);
        Io(std::io::Error);
        SystemTime(std::time::SystemTimeError);
    }
}

fn main() -> Result<()> {
    for entry in WalkDir::new(".")
            .follow_links(true)
            .into_iter()
            .filter_map(|e| e.ok()) {
        let f_name = entry.file_name().to_string_lossy();
        let sec = entry.metadata()?.modified()?;

        if f_name.ends_with(".json") && sec.elapsed()?.as_secs() < 86400 {
            println!("{}", f_name);
        }
    }

    Ok(())
}
```

### Обход директорий с пропуском скрытых файлов

Используем метод `filter_entry` для рекурсивного перебора сущностей. Функция `is_not_hidden` возвращает индикатор того, является ли файл или директория скрытыми (если название сущности начинается с точки, значит сущность является скрытой).

```rust
use walkdir::{DirEntry, WalkDir};

fn is_not_hidden(entry: &DirEntry) -> bool {
    entry
        .file_name()
        .to_str()
        .map(|s| entry.depth() == 0 || !s.starts_with("."))
        .unwrap_or(false)
}

fn main() {
    WalkDir::new(".")
        .into_iter()
        .filter_entry(|e| is_not_hidden(e))
        .filter_map(|v| v.ok())
        .for_each(|x| println!("{}", x.path().display()));
}
```

### Рекурсивное вычисление размера файлов до заданной глубины

Глубина рекурсии может быть гибко установлена с помощью методов `WalkDir::min_depth` и `WalkDir::max_depth`. Вычисляем размер файлов на глубине трех поддиректорий, игнорируя файлы в корневой директории:

```rust
use walkdir::WalkDir;

fn main() {
    let total_size = WalkDir::new(".")
        .min_depth(1)
        .max_depth(3)
        .into_iter()
        .filter_map(|entry| entry.ok())
        .filter_map(|entry| entry.metadata().ok())
        .filter(|metadata| metadata.is_file())
        .fold(0, |acc, m| acc + m.len());

    println!("Общий размер: {} байтов.", total_size);
}
```

### Рекурсивный поиск всех файлов PNG

Пример рекурсивного поиска всех файлов PNG в текущей директории. Паттерн `**` совпадает с текущей директорией и всеми ее поддиректориями.

```rust
use error_chain::error_chain;

use glob::glob;

error_chain! {
    foreign_links {
        Glob(glob::GlobError);
        Pattern(glob::PatternError);
    }
}

fn main() -> Result<()> {
    for entry in glob("**/*.png")? {
        println!("{}", entry?.display());
    }

    Ok(())
}
```

### Поиск файлов PNG, совпадающих с заданным паттерном

Пример поиска всех изображений в директории `media`, совпадающих с паттерном `img_[0-9]*.png`. В функцию `glob_with` передается структура `MatchOptions` с настройкой `case_sensitive: false`.

```rust
use error_chain::error_chain;
use glob::{glob_with, MatchOptions};

error_chain! {
    foreign_links {
        Glob(glob::GlobError);
        Pattern(glob::PatternError);
    }
}

fn main() -> Result<()> {
    let options = MatchOptions {
        case_sensitive: false,
        ..Default::default()
    };

    for entry in glob_with("/media/img_[0-9]*.png", options)? {
        println!("{}", entry?.display());
    }

    Ok(())
}
```
