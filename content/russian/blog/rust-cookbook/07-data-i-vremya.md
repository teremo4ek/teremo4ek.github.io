---
title: "Дата и время"
description: "Продолжительность, вычисление, разбор и форматирование даты и времени"
date: 2026-05-14T05:00:00Z
weight: 7
image: "/images/image-placeholder.png"
categories: ["Rust"]
tags: ["rust", "дата и время"]
---

## Продолжительность и вычисление даты и времени

### Измерение прошедшего времени

Пример измерения `time::Instant::elapsed`, прошедшего с `time::Instant::now`. Метод `time::Instant::elapsed` возвращает `time::Duration`. Вызов этого метода не меняет и не сбрасывает объект `time::Instant`.

```rust
use std::time::{Duration, Instant};
use std::thread;

fn expensive_function() {
    thread::sleep(Duration::from_secs(1));
}

fn main() {
    let start = Instant::now();
    expensive_function();
    let duration = start.elapsed();

    println!("Time elapsed in expensive_function() is: {:?}", duration);
}
```

### Вычисление даты и времени

Пример вычисления даты и времени через две недели от текущих с помощью `DateTime::checked_add_signed` и даты предшествующего дня с помощью `DateTime::checked_sub_signed`. Эти методы возвращают `None`, если дата и время не могут быть вычислены.

```rust
use chrono::{DateTime, Duration, Utc};

fn day_earlier(date_time: DateTime<Utc>) -> Option<DateTime<Utc>> {
    date_time.checked_sub_signed(Duration::days(1))
}

fn main() {
    let now = Utc::now();
    println!("{}", now);

    let almost_three_weeks_from_now = now.checked_add_signed(Duration::weeks(2))
            .and_then(|in_2weeks| in_2weeks.checked_add_signed(Duration::weeks(1)))
            .and_then(day_earlier);

    match almost_three_weeks_from_now {
        Some(x) => println!("{}", x),
        None => eprintln!("Almost three weeks from now overflows!"),
    }

    match now.checked_add_signed(Duration::max_value()) {
        Some(x) => println!("{}", x),
        None => eprintln!("We can't use chrono to tell the time for the Solar System to complete more than one full orbit around the galactic center."),
    }
}
```

### Преобразование локального времени в другую временную зону

Пример получения локального времени с помощью `offset::Local::now` и его преобразование в UTC с помощью `DateTime::from_utc`. Затем UTC-время преобразуется в UTC+8 и UTC-2 с помощью `offset::FixedOffset`.

```rust
use chrono::{DateTime, FixedOffset, Local, Utc};

fn main() {
    let local_time = Local::now();
    let utc_time = DateTime::<Utc>::from_utc(local_time.naive_utc(), Utc);
    let china_timezone = FixedOffset::east(8 * 3600);
    let rio_timezone = FixedOffset::west(2 * 3600);
    println!("Local time now is {}", local_time);
    println!("UTC time now is {}", utc_time);
    println!(
        "Time in Hong Kong now is {}",
        utc_time.with_timezone(&china_timezone)
    );
    println!("Time in Rio de Janeiro now is {}", utc_time.with_timezone(&rio_timezone));
}
```

## Разбор и отображение даты и времени

### Получение даты и времени

Пример получения текущего `DateTime` в формате UTC, его часов/минут/секунд через `Timelike` и лет/месяцев/дней недели через `Datelike`:

```rust
use chrono::{Datelike, Timelike, Utc};

fn main() {
    let now = Utc::now();

    let (is_pm, hour) = now.hour12();
    println!(
        "The current UTC time is {:02}:{:02}:{:02} {}",
        hour,
        now.minute(),
        now.second(),
        if is_pm { "PM" } else { "AM" }
    );
    println!(
        "And there have been {} seconds since midnight",
        now.num_seconds_from_midnight()
    );

    let (is_common_era, year) = now.year_ce();
    println!(
        "The current UTC date is {}-{:02}-{:02} {:?} ({})",
        year,
        now.month(),
        now.day(),
        now.weekday(),
        if is_common_era { "CE" } else { "BCE" }
    );
    println!(
        "And the Common Era began {} days ago",
        now.num_days_from_ce()
    );
}
```

### Преобразование даты в метку времени UNIX и наоборот

Пример преобразования даты из `NaiveDate::from_ymd` и `NaiveTime::from_hms` в метку времени (timestamp) UNIX с помощью `NaiveDateTime::timestamp` и вычисления даты спустя миллиард секунд после 1970-01-01 0:00:00 UTC с помощью `NaiveDateTime::from_timestamp`.

```rust
use chrono::{NaiveDate, NaiveDateTime};

fn main() {
    let date_time: NaiveDateTime = NaiveDate::from_ymd(2017, 11, 12).and_hms(17, 33, 44);
    println!(
        "Количество секунд между 1970-01-01 00:00:00 и {} равняется {}.",
        date_time, date_time.timestamp());

    let date_time_after_a_billion_seconds = NaiveDateTime::from_timestamp(1_000_000_000, 0);
    println!(
        "Дата через миллиард секунд после 1970-01-01 00:00:00: {}.",
        date_time_after_a_billion_seconds);
}
```

### Форматирование даты и времени

Пример получения текущей даты в формате UTC с помощью `Utc::now` и ее форматирование в популярные форматы RFC 2822 с помощью `DateTime::to_rfc2822` и RFC 3339 с помощью `DateTime::to_rfc3339`, а также в кастомный формат с помощью `DateTime::format`:

```rust
use chrono::{DateTime, Utc};

fn main() {
    let now: DateTime<Utc> = Utc::now();

    println!("UTC now is: {}", now);
    println!("UTC now in RFC 2822 is: {}", now.to_rfc2822());
    println!("UTC now in RFC 3339 is: {}", now.to_rfc3339());
    println!("UTC now in a custom format is: {}", now.format("%a %b %e %T %Y"));
}
```

### Преобразование строки в структуру DateTime

Пример преобразования строк в структуры `DateTime`, представляющие популярные форматы RFC 2822, RFC 3339 и кастомный формат с помощью `DateTime::parse_from_rfc2822`, `DateTime::parse_from_rfc3339` и `DateTime::parse_from_str`.

```rust
use chrono::{DateTime, NaiveDate, NaiveDateTime, NaiveTime};
use chrono::format::ParseError;

fn main() -> Result<(), ParseError> {
    let rfc2822 = DateTime::parse_from_rfc2822("Tue, 1 Jul 2003 10:52:37 +0200")?;
    println!("{}", rfc2822);

    let rfc3339 = DateTime::parse_from_rfc3339("1996-12-19T16:39:57-08:00")?;
    println!("{}", rfc3339);

    let custom = DateTime::parse_from_str("5.8.1994 8:00 am +0000", "%d.%m.%Y %H:%M %P %z")?;
    println!("{}", custom);

    let time_only = NaiveTime::parse_from_str("23:56:04", "%H:%M:%S")?;
    println!("{}", time_only);

    let date_only = NaiveDate::parse_from_str("2015-09-05", "%Y-%m-%d")?;
    println!("{}", date_only);

    let no_timezone = NaiveDateTime::parse_from_str("2015-09-05 23:56:04", "%Y-%m-%d %H:%M:%S")?;
    println!("{}", no_timezone);

    Ok(())
}
```
