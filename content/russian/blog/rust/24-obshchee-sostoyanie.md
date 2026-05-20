---
title: "Общее состояние"
description: "Mutex, RwLock, Arc, Atomics"
date: 2026-05-20T05:00:00Z
weight: 24
image: "/images/rust/24-obshchee-sostoyanie-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


`Rust` использует систему типов для обеспечения синхронизации общих (shared) данных. Это делается в основном с помощью двух типов:

- [`Arc<T>`](https://doc.rust-lang.org/std/sync/struct.Arc.html) - атомарный счетчик ссылок на `T`: обрабатывает передачу между потоками и освобождает `T` при уничтожении последней ссылки на нее
- [`Mutex<T>`](https://doc.rust-lang.org/std/sync/struct.Mutex.html) - обеспечивает взаимоисключающий доступ к значению `T`

__Arc__

`Arc<T>` предоставляет общий доступ только для чтения к `T` через `Arc::clone()`:

```rust
use std::sync::Arc;
use std::thread;

fn main() {
    let v = Arc::new(vec![10, 20, 30]);
    let mut handles = Vec::new();
    for _ in 1..5 {
        let v = Arc::clone(&v);
        handles.push(thread::spawn(move || {
            let thread_id = thread::current().id();
            println!("{thread_id:?}: {v:?}");
        }));
    }

    handles.into_iter().for_each(|h| h.join().unwrap());
    println!("v: {v:?}");
}
```

Ремарки:

- `Arc` означает Atomic Reference Counter (атомарный счетчик ссылок) и является потокобезопасной версией `Rc`, в которой используются атомарные операции
- `Arc<T>` реализует `Clone` независимо от того, делает ли это `T`. Он реализует `Send` и `Sync`, только если `T` их реализует
- `Arc::clone()` имеет некоторую цену за счет выполнения атомарных операций, но после этого использование `T` является бесплатным
- остерегайтесь ссылочных циклов, `Arc` не использует сборщик мусора для их обнаружения
  - в этом может помочь `std::sync::Weak`

__Mutex__

`Mutex<T>` обеспечивает взаимное исключение и предоставляет мутабельный доступ к `T` через доступный только для чтения интерфейс (форма внутренней изменчивости):

```rust
use std::sync::Mutex;

fn main() {
    let v = Mutex::new(vec![10, 20, 30]);
    println!("v: {:?}", v.lock().unwrap());

    {
        let mut guard = v.lock().unwrap();
        guard.push(40);
    }

    println!("v: {:?}", v.lock().unwrap());
}
```

Обратите внимание на неявную реализацию (`impl<T: Send> Sync for Mutex<T>`)[https://doc.rust-lang.org/std/sync/struct.Mutex.html#impl-Sync-for-Mutex%3CT%3E](https://doc.rust-lang.org/std/sync/struct.Mutex.html#impl-Sync-for-Mutex%3CT%3E).

Ремарки:

- `Mutex` в `Rust` похож на коллекцию, состоящую из одного элемента - защищенных данных
  - невозможно забыть получить (acquire) мьютекс перед доступом к защищенным данным
- из `&Mutex<T>` через блокировку (lock) можно получить `&mut T`. `MutexGuard` гарантирует, что `&mut T` не живет дольше удерживаемой (held) блокировки
- `Mutex<T>` реализует `Send` и `Sync`, только если `T` реализует `Send`
- `RwLock` является блокировкой, доступной как для чтения, так и для записи
- почему `lock()` возвращает `Result`?
  - Если поток, в котором находится мьютекс, паникует, мьютекс становится "отравленным" (poisoned), сигнализируя о том, что защищенные данные могут находиться в несогласованном состоянии. Вызов `lock()` на отравленном мьютексе проваливается с [PoisonError](https://doc.rust-lang.org/std/sync/struct.PoisonError.html). Для восстановления данных можно вызвать `into_iter()` на ошибке

__Пример__

Рассмотрим `Arc` и `Mutex` в действии:

```rust
use std::thread;
// use std::sync::{Arc, Mutex};

fn main() {
    let v = vec![10, 20, 30];
    let handle = thread::spawn(|| {
        v.push(10);
    });
    v.push(1000);

    handle.join().unwrap();
    println!("v: {v:?}");
}
```

Возможное решение:

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let v = Arc::new(Mutex::new(vec![10, 20, 30]));

    let v2 = Arc::clone(&v);
    let handle = thread::spawn(move || {
        let mut v2 = v2.lock().unwrap();
        v2.push(10);
    });

    {
        let mut v = v.lock().unwrap();
        v.push(1000);
    }

    handle.join().unwrap();

    println!("v: {v:?}");
}
```

Ремарки:

- `v` обернут в `Arc` и `Mutex`, поскольку их зоны ответственности ортогональны
  - оборачивание `Mutex` в `Arc` является распространенным паттерном для передачи мутабельного состояния между потоками
- `v: Arc<_>` должен быть клонирован как `v2` для передачи в другой поток. Обратите внимание на `move` в сигнатуре лямбды
- блоки предназначены для максимального сужения области видимости `LockGuard`
