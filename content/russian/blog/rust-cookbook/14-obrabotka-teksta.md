---
title: "Обработка текста"
description: "Регулярные выражения и разбор строк в Rust"
date: 2026-05-14T05:00:00Z
weight: 14
image: "/images/rust-cookbook/14-obrabotka-teksta-cover.png"
categories: ["Rust"]
tags: ["rust", "обработка текста"]
---

## Регулярные выражения

### Проверка и извлечение логина из адреса email

Пример валидации email и извлечения всего, что предшествует `@`:

```rust
use lazy_static::lazy_static;
use regex::Regex;

fn extract_login(input: &str) -> Option<&str> {
    lazy_static! {
        static ref RE: Regex = Regex::new(r"(?x)
            ^(?P<login>[^@\s]+)@
            ([[:word:]]+\.)*
            [[:word:]]+$
            ").unwrap();
    }
    RE.captures(input).and_then(|cap| {
        cap.name("login").map(|login| login.as_str())
    })
}

fn main() {
    assert_eq!(extract_login(r"I❤email@example.com"), Some(r"I❤email"));
    assert_eq!(
        extract_login(r"sdf+sdsfsd.as.sdsd@jhkk.d.rl"),
        Some(r"sdf+sdsfsd.as.sdsd")
    );
    assert_eq!(extract_login(r"More@Than@One@at.com"), None);
    assert_eq!(extract_login(r"Not an email@email"), None);
}
```

### Извлечение списка уникальных хештегов из текста

Пример извлечения, сортировки и удаления дублирующихся хештегов из текста. Регулярное выражение для проверки хештега учитывает только латинские хештеги, которые начинаются с буквы.

```rust
use lazy_static::lazy_static;

use regex::Regex;
use std::collections::HashSet;

fn extract_hashtags(text: &str) -> HashSet<&str> {
    lazy_static! {
        static ref RE: Regex = Regex::new(
                r"\#[a-zA-Z][0-9a-zA-Z_]*"
            ).unwrap();
    }
    RE.find_iter(text).map(|mat| mat.as_str()).collect()
}

fn main() {
    let tweet = "Hey #world, I just got my new #dog, say hello to Till. #dog #forever #2 #_ ";
    let tags = extract_hashtags(tweet);
    assert!(tags.contains("#dog") && tags.contains("#forever") && tags.contains("#world"));
    assert_eq!(tags.len(), 3);
}
```

### Извлечение из текста номеров телефона

Пример обработки текста с помощью `Regex::captures_iter` для захвата нескольких номеров телефона. Регулярное выражение учитывает только американские номера.

```rust
use error_chain::error_chain;

use regex::Regex;
use std::fmt;

error_chain!{
    foreign_links {
        Regex(regex::Error);
        Io(std::io::Error);
    }
}

struct PhoneNumber<'a> {
    area: &'a str,
    exchange: &'a str,
    subscriber: &'a str,
}

impl<'a> fmt::Display for PhoneNumber<'a> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "1 ({}) {}-{}", self.area, self.exchange, self.subscriber)
    }
}

fn main() -> Result<()> {
    let phone_text = "
    +1 505 881 9292 (v) +1 505 778 2212 (c) +1 505 881 9297 (f)
    (202) 991 9534
    Alex 5553920011
    1 (800) 233-2010
    1.299.339.1020";

    let re = Regex::new(
        r#"(?x)
          (?:\+?1)?                       # опциональный код страны
          [\s\.]?
          (([2-9]\d{2})|\(([2-9]\d{2})\)) # код региона
          [\s\.\-]?
          ([2-9]\d{2})                    # код обмена
          [\s\.\-]?
          (\d{4})                         # код подписчика"#,
    )?;

    let phone_numbers = re.captures_iter(phone_text).filter_map(|cap| {
        let groups = (cap.get(2).or(cap.get(3)), cap.get(4), cap.get(5));
        match groups {
            (Some(area), Some(ext), Some(sub)) => Some(PhoneNumber {
                area: area.as_str(),
                exchange: ext.as_str(),
                subscriber: sub.as_str(),
            }),
            _ => None,
        }
    });

    assert_eq!(
        phone_numbers.map(|m| m.to_string()).collect::<Vec<_>>(),
        vec![
            "1 (505) 881-9292",
            "1 (505) 778-2212",
            "1 (505) 881-9297",
            "1 (202) 991-9534",
            "1 (555) 392-0011",
            "1 (800) 233-2010",
            "1 (299) 339-1020",
        ]
    );

    Ok(())
}
```

### Замена всех подстрок в строке

Пример замены всех стандартных дат ISO 8601 `YYYY-MM-DD` эквивалентными датами в привычном формате. Например `2013-01-15` становится `15.01.2013`. Метод `Regex::replace_all` заменяет все вхождения всего регулярного выражения.

```rust
use lazy_static::lazy_static;

use std::borrow::Cow;
use regex::Regex;

fn reformat_dates(before: &str) -> Cow<str> {
    lazy_static! {
        static ref RE : Regex = Regex::new(
            r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})"
            ).unwrap();
    }
    RE.replace_all(before, "$d.$m.$y")
}

fn main() {
    let before = "2012-03-14, 2013-01-15 и 2014-07-05";
    let after = reformat_dates(before);
    assert_eq!(after, "14.03.2012, 15.01.2013 и 05.07.2014");
}
```

## Разбор строки

### Сбор графем Юникода

Собираем индивидуальные графемы Юникода из UTF-8 строки с помощью метода `UnicodeSegmentation::graphemes` из крейта `unicode-segmentation`:

```rust
use unicode_segmentation::UnicodeSegmentation;

fn main() {
    let name = "Йогурт захватил мир\r\n";
    let graphemes = UnicodeSegmentation::graphemes(name, true)
    	.collect::<Vec<&str>>();
    assert_eq!(graphemes[0], "Й");
}
```

### Реализация трейта FromStr для кастомной структуры

Создаем кастомную структуру `RGB` и реализуем на ней трейт `FromStr` для преобразования цвета HEX в цвет RGB:

```rust
use std::str::FromStr;

#[derive(Debug, PartialEq)]
struct RGB {
    r: u8,
    g: u8,
    b: u8,
}

impl FromStr for RGB {
    type Err = std::num::ParseIntError;

    fn from_str(hex_code: &str) -> Result<Self, Self::Err> {
        let r: u8 = u8::from_str_radix(&hex_code[1..3], 16)?;
        let g: u8 = u8::from_str_radix(&hex_code[3..5], 16)?;
        let b: u8 = u8::from_str_radix(&hex_code[5..7], 16)?;

        Ok(RGB { r, g, b })
    }
}

fn main() {
    let code = "#fa7268";
    match RGB::from_str(code) {
        Ok(rgb) => {
            println!(
                "The RGB color code is: R: {} G: {} B: {}",
                rgb.r, rgb.g, rgb.b
            );
        }
        Err(_) => {
            println!("{} is not a valid color hex code!", code);
        }
    }

    assert_eq!(
        RGB::from_str(&r"#fa7268").unwrap(),
        RGB {
            r: 250,
            g: 114,
            b: 104
        }
    );
}
```
