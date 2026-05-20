---
title: "Каналы"
description: "Каналы передачи сообщений, mpsc, multipart"
date: 2026-05-20T05:00:00Z
weight: 22
image: "/images/rust/22-kanaly-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


Каналы (channels) `Rust` состоят из двух частей: `Sender<T>` (отправитель/передатчик) и `Receiver<T>` (получатель/приемник). Они соединяются с помощью канала, но мы видим только конечные точки:

```rust
use std::sync::mpsc;

fn main() {
    let (tx, rx) = mpsc::channel();

    tx.send(10).unwrap();
    tx.send(20).unwrap();

    println!("Получено: {:?}", rx.recv());
    println!("Получено: {:?}", rx.recv());

    let tx2 = tx.clone();
    tx2.send(30).unwrap();
    println!("Получено: {:?}", rx.recv());
}
```

- `mpsc` означает Multi-Producer, Single-Consumer (несколько производителей, один потребитель). `Sender` и `SyncSender` реализуют `Clone` (поэтому мы можем создать несколько производителей), а `Receiver` не реализует (поэтому у нас может быть только один потребитель)
- `send()` и `recv()` возвращают `Result`. Если они возвращают `Err`, значит соответствующий `Sender` или `Receiver` уничтожен (dropped) и канал закрыт

__Несвязанные каналы__

`mpsc::channel()` возвращает несвязанный (unbounded) и асинхронный канал:

```rust
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        let thread_id = thread::current().id();
        for i in 1..10 {
            tx.send(format!("Сообщение {i}")).unwrap();
            println!("{thread_id:?}: отправил сообщение {i}");
        }
        println!("{thread_id:?}: готово");
    });
    thread::sleep(Duration::from_millis(100));

    for msg in rx.iter() {
        println!("Основной поток: получено {msg}");
    }
}
```

__Связанные каналы__

`send()` связанного (bounded) синхронного канала блокирует текущий поток:

```rust
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::sync_channel(3);

    thread::spawn(move || {
        let thread_id = thread::current().id();
        for i in 1..10 {
            tx.send(format!("Сообщение {i}")).unwrap();
            println!("{thread_id:?}: отправил сообщение {i}");
        }
        println!("{thread_id:?}: готово");
    });
    thread::sleep(Duration::from_millis(100));

    for msg in rx.iter() {
        println!("Основной поток: получено {msg}");
    }
}
```

Ремарки:

- вызов `send()` блокирует текущий поток до тех пор, пока в канале имеется место для новых сообщений. Поток может блокироваться бесконечно, если отсутствует получатель
- вызов `send()` заканчивается ошибкой (поэтому возвращается `Result`), если канал закрыт. Канал закрывается после уничтожения получателя
- связанный канал с нулевым размером называется "rendezvous channel". Каждый вызов `send()` блокирует текущий поток, пока другой поток не вызовет `read()`
