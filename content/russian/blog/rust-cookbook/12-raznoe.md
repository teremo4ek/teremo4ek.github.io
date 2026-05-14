---
title: "Разное"
description: "Количество ядер CPU, лениво оцениваемые константы и обработка запросов на неиспользуемом порту"
date: 2026-05-14T05:00:00Z
weight: 12
image: "/images/image-placeholder.png"
categories: ["Rust"]
tags: ["rust", "разное"]
---

## Проверка количества логических ядер центрального процессора

```rust
fn main() {
    println!("Количество логических ядер ЦП: {}", num_cpus::get());
}
```

## Определение лениво оцениваемой константы

Пример определения лениво оцениваемой (lazy evaluated) константной `HashMap`. `HashMap` оценивается один раз и хранится за глобальной статической ссылкой.

```rust
use lazy_static::lazy_static;
use std::collections::HashMap;

lazy_static! {
    static ref PRIVILEGES: HashMap<&'static str, Vec<&'static str>> = {
        let mut map = HashMap::new();
        map.insert("Игорь", vec!["user", "admin"]);
        map.insert("Алекс", vec!["user"]);
        map
    };
}

fn show_access(name: &str) {
    let access = PRIVILEGES.get(name);
    println!("{}: {:?}", name, access);
}

fn main() {
    let access = PRIVILEGES.get("Игорь");
    println!("Игорь: {:?}", access);

    show_access("Алекс");
}
```

## Обработка запросов на неиспользуемом порту

В следующем примере порт отображается в терминале и программа принимает подключения до получения запроса. При установке порта в значение 0, `SocketAddrV4` присваивает произвольный порт.

```rust
use std::net::{SocketAddrV4, Ipv4Addr, TcpListener};
use std::io::{Read, Error};

fn main() -> Result<(), Error> {
    let loopback = Ipv4Addr::new(127, 0, 0, 1);
    let socket = SocketAddrV4::new(loopback, 0);
    let listener = TcpListener::bind(socket)?;
    let port = listener.local_addr()?;
    println!("Listening on {}, access this port to end the program", port);
    let (mut tcp_stream, addr) = listener.accept()?;
    println!("Connection received! {:?} is sending data.", addr);
    let mut input = String::new();
    let _ = tcp_stream.read_to_string(&mut input)?;
    println!("{:?} says {}", addr, input);
    Ok(())
}
```
