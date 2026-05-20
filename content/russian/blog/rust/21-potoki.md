---
title: "Потоки"
description: "Создание потоков, scoped threads, move-замыкания"
date: 2026-05-20T05:00:00Z
weight: 21
image: "/images/rust/21-potoki-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


Потоки (threads) `Rust` работают аналогично потокам в других языках:

```rust
use std::thread;
use std::time::Duration;

fn main() {
    thread::spawn(|| {
        for i in 1..10 {
            println!("значение счетчика в выделенном потоке: {i}!");
            thread::sleep(Duration::from_millis(5));
        }
    });

    for i in 1..5 {
        println!("значение счетчика в основном потоке: {i}");
        thread::sleep(Duration::from_millis(5));
    }
}
```

- потоки являются потоками демона (daemon threads), основной поток не ждет их выполнения
- потоки паникуют независимо друг от друга
  - паника может содержать полезную нагрузку (payload), которую можно извлечь с помощью `downcast_ref`

Ремарки:

- обратите внимание, что основной поток не ждет выполнения выделенных (spawned) потоков
- для ожидания выполнения потока следует использовать `let handle = thread::spawn()` и затем `handle.join()`
- вызовите панику в потоке. Обратите внимание, что это не влияет на `main`
- используйте `Result`, возвращаемый из `handle.join()`, для доступа к полезной нагрузке паники. В этом может помочь [Any](https://doc.rust-lang.org/std/any/index.html)

__Потоки с ограниченной областью видимости__

Обычные потоки не могут заимствовать значения из окружения:

```rust
use std::thread;

fn foo() {
    let s = String::from("привет");
    thread::spawn(|| {
        println!("длина: {}", s.len());
    });
}

fn main() {
    foo();
}
```

Однако для этого можно использовать [scoped threads](https://doc.rust-lang.org/std/thread/fn.scope.html) (потоки с ограниченной областью видимости):

```rust
use std::thread;

fn main() {
    let s = String::from("привет");

    thread::scope(|scope| {
        scope.spawn(|| {
            println!("длина: {}", s.len());
        });
    });
}
```

Ремарки:

- когда функция `thread::scope` завершается, все потоки гарантированно объединяются, поэтому они могут вернуть заимствованные данные
- применяются обычные правила заимствования `Rust`: мы можем заимствовать значение мутабельно в одном потоке, или иммутабельно в любом количестве потоков
