---
title: "Командная строка"
description: "Разбор аргументов командной строки и работа с ANSI-терминалом в Rust"
date: 2026-05-14T05:00:00Z
weight: 2
image: "/images/image-placeholder.png"
categories: ["Rust"]
tags: ["rust", "cli"]
---

## Разбор аргументов командной строки

Пример разбора (parsing) аргументов командной строки с помощью крейта `clap`:

```rust
use clap::{Arg, Command};

fn main() {
    let matches = Command::new("My Test Program")
        .version("0.1.0")
        .author("Harry Heman")
        .about("Command line argument parsing")
        // файл
        .arg(
            Arg::new("file")
                .short('f')
                .long("file")
                .help("Файл"),
        )
        // число
        .arg(
            Arg::new("num")
                .short('n')
                .long("number")
                .help("Ваше любимое число"),
        )
        .get_matches();

    let myfile = matches.get_one::<String>("file").unwrap();
    println!("Файл: {}", myfile);

    let num_str = matches.get_one::<String>("num");
    match num_str {
        None => println!("Ваше любимое число неизвестно"),
        Some(s) => match s.parse::<i32>() {
            Ok(n) => println!("Ваше любимое число: {}", n),
            Err(_) => println!("Это не число: {}", s),
        },
    }
}
```

Команда для запуска программы:

```bash
cargo run -- -f myfile.txt -n 42
```

Вывод:

```
Файл: myfile.txt
Ваше любимое число: 42
```

## ANSI-терминал

Пример использования крейта `ansi_term` для управления цветом и форматированием текста в терминале. `ansi_term` предоставляет две основные структуры: `ANSIString` и `Style`. `Style` содержит информацию о стилях: цвет, вес текста и др. Существуют также варианты `Colour` (британский вариант color), представляющие простые цвета текста. `ANSIString` — это пара из строки и `Style`.

### Печать цветного текста

```rust
use ansi_term::Colour;

fn main() {
    println!("This is {} in color, {} in color and {} in color",
        Colour::Red.paint("red"),
        Colour::Blue.paint("blue"),
        Colour::Green.paint("green"));
}
```

### Печать жирного текста

Для более сложной стилизации, чем изменение цвета, необходимо использовать экземпляр `Style`. Он создается с помощью метода `Style::new`.

```rust
use ansi_term::Style;

fn main() {
    println!("{} and this is not",
        Style::new().bold().paint("This is Bold"));
}
```

### Печать жирного и цветного текста

`Colour` реализует множество методов, похожих на методы `Style`.

```rust
use ansi_term::Colour;
use ansi_term::Style;

fn main(){
    println!("{}, {} and {}",
        Colour::Yellow.paint("This is colored"),
        Style::new().bold().paint("this is bold"),
        Colour::Yellow.bold().paint("this is bold and colored"));
}
```
