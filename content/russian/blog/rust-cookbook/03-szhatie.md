---
title: "Сжатие"
description: "Работа с tarball-архивами: распаковка, сжатие и удаление префиксов путей"
date: 2026-05-14T05:00:00Z
weight: 3
image: "/images/image-placeholder.png"
categories: ["Rust"]
tags: ["rust", "сжатие", "архивы"]
---

## Работа с tarball

### Распаковка tarball

Пример распаковки (`GzDecoder`) и извлечения (`Archive::unpack`) всех файлов из сжатого tarball `archive.tar.gz`, находящегося в текущей рабочей директории:

```rust
use flate2::read::GzDecoder;
use std::fs::File;
use tar::Archive;

fn main() -> Result<(), std::io::Error> {
    let path = "archive.tar.gz";
    let tar_gz = File::open(path)?;
    let tar = GzDecoder::new(tar_gz);
    let mut archive = Archive::new(tar);
    archive.unpack(".")?;

    Ok(())
}
```

### Сжатие директории в tarball

Пример сжатия директории `/var/log` в `archive.tar.gz`. Создаем `File`, обернутый в `GzEncoder` и `tar::Builder`. Рекурсивно помещаем содержимое директории `/var/log` в архив, находящийся в `backup/logs` с помощью `Builder::append_dir_all`. `GzEncoder` отвечает за сжатие данных перед их записью в `archive.tar.gz`.

```rust
use flate2::write::GzEncoder;
use flate2::Compression;
use std::fs::File;

fn main() -> Result<(), std::io::Error> {
    let tar_gz = File::create("archive.tar.gz")?;
    let enc = GzEncoder::new(tar_gz, Compression::default());
    let mut tar = tar::Builder::new(enc);
    tar.append_dir_all("backup/logs", "/var/log")?;
    Ok(())
}
```

### Распаковка tarball с удалением префикса пути

Перебираем файлы с помощью метода `Archive::entries`. Используем метод `Path::strip_prefix` для удаления префикса пути (`bundle/logs`). Наконец, извлекаем `tar::Entry` с помощью метода `Entry::unpack`.

```rust
use error_chain::error_chain;
use std::fs::File;
use std::path::PathBuf;
use flate2::read::GzDecoder;
use tar::Archive;

error_chain! {
  foreign_links {
    Io(std::io::Error);
    StripPrefixError(std::path::StripPrefixError);
  }
}

fn main() -> Result<()> {
    let file = File::open("archive.tar.gz")?;
    let mut archive = Archive::new(GzDecoder::new(file));
    let prefix = "bundle/logs";

    println!("Extracted the following files:");
    archive
        .entries()?
        .filter_map(|e| e.ok())
        .map(|mut entry| -> Result<PathBuf> {
            let path = entry.path()?.strip_prefix(prefix)?.to_owned();
            entry.unpack(&path)?;
            Ok(path)
        })
        .filter_map(|e| e.ok())
        .for_each(|x| println!("> {}", x.display()));

    Ok(())
}
```
