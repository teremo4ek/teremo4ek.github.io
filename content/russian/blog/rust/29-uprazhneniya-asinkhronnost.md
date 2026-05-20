---
title: "Упражнения: Асинхронность"
description: "Практические задачи по асинхронному программированию"
date: 2026-05-20T05:00:00Z
weight: 29
image: "/images/rust/29-uprazhneniya-asinkhronnost-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


Для тренировки навыков работы с асинхронным `Rust`, есть еще два упражнения:

- обедающие философы - на этот раз вам нужно решить эту задачу с помощью асинхронного `Rust`
- приложение для чата

__Обедающие философы__

```rust
use std::sync::Arc;
use tokio::sync::mpsc::{self, Sender};
use tokio::sync::Mutex;
use tokio::time;

struct Fork;

struct Philosopher {
    name: String,
    // left_fork: ...
    // right_fork: ...
    // thoughts: ...
}

impl Philosopher {
    async fn think(&self) {
        self.thoughts
            .send(format!("Эврика! {} сгенерировал(а) новую идею!", &self.name))
            .await
            .unwrap();
    }

    async fn eat(&self) {
        // Пытаемся до тех пор, пока не получим обе вилки
        println!("{} ест...", &self.name);
        time::sleep(time::Duration::from_millis(5)).await;
    }
}

static PHILOSOPHERS: &[&str] =
     &["Сократ", "Гипатия", "Платон", "Аристотель", "Пифагор"];

#[tokio::main]
async fn main() {
    // Создаем вилки

    // Создаем философов

    // Каждый философ размышляет и ест 100 раз

    // Выводим размышления философов
}
```

Для работы с асинхронным `Rust` рекомендуется использовать `tokio`:

```toml
[package]
name = "dining-philosophers-async"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1.26.0", features = ["sync", "time", "macros", "rt-multi-thread"] }
```

Подсказка: на этот раз вам придется использовать `Mutex` и модуль `mpsc` из `tokio`.

<details>
<summary>Решение:</summary>

```rust
use std::sync::Arc;
use tokio::sync::mpsc::{self, Sender};
use tokio::sync::Mutex;
use tokio::time;

struct Fork;

struct Philosopher {
    name: String,
    left_fork: Arc<Mutex<Fork>>,
    right_fork: Arc<Mutex<Fork>>,
    thoughts: Sender<String>,
}

impl Philosopher {
    async fn think(&self) {
        self.thoughts
            .send(format!("Эврика! {} сгенерировал(а) новую идею!", &self.name))
            .await
            .unwrap();
    }

    async fn eat(&self) {
         // Пытаемся до тех пор, пока не получим обе вилки
        let (_left_fork, _right_fork) = loop {
            // Берем вилки...
            let left_fork = self.left_fork.try_lock();
            let right_fork = self.right_fork.try_lock();

            let Ok(left_fork) = left_fork else {
                // Если мы не получили левую вилку, удаляем правую вилку,
                // если она у нас была, позволяя выполняться другим задачам
                drop(right_fork);
                time::sleep(time::Duration::from_millis(1)).await;
                continue;
            };

            let Ok(right_fork) = right_fork else {
                // Если мы не получили правую вилку, удаляем левую вилку,
                // если она у нас была, позволяя выполняться другим задачам
                drop(left_fork);
                time::sleep(time::Duration::from_millis(1)).await;
                continue;
            };

            break (left_fork, right_fork);
        };

        println!("{} ест...", &self.name);
        time::sleep(time::Duration::from_millis(5)).await;
        // Блокировки уничтожаются здесь
    }
}

static PHILOSOPHERS: &[&str] =
   &["Сократ", "Гипатия", "Платон", "Аристотель", "Пифагор"];

#[tokio::main]
async fn main() {
    // Создаем вилки
    let mut forks = vec![];
    (0..PHILOSOPHERS.len()).for_each(|_| forks.push(Arc::new(Mutex::new(Fork))));

    // Создаем философов
    let (philosophers, mut rx) = {
        let mut philosophers = vec![];

        let (tx, rx) = mpsc::channel(10);

        for (i, name) in PHILOSOPHERS.iter().enumerate() {
            let left_fork = Arc::clone(&forks[i]);
            let right_fork = Arc::clone(&forks[(i + 1) % PHILOSOPHERS.len()]);

            philosophers.push(Philosopher {
                name: name.to_string(),
                left_fork,
                right_fork,
                thoughts: tx.clone(),
            });
        }

        (philosophers, rx)
        // `tx` уничтожается здесь, поэтому нам не нужно явно удалять его позже
    };

    // Каждый философ думает и ест 100 раз
    for phil in philosophers {
        tokio::spawn(async move {
            for _ in 0..100 {
                phil.think().await;
                phil.eat().await;
            }
        });
    }

    // Выводим размышления философов
    while let Some(thought) = rx.recv().await {
        println!("{thought}");
    }
}
```

</details>

__Чат__

В этом упражнении мы используем новые знания для разработки приложения чата. У нас есть сервер, к которому подключаются клиенты и в котором они публикуют свои сообщения. Клиент читает пользовательские сообщения через стандартный ввод и отправляет их на сервер. Сервер передает (broadcast) сообщение всем клиентам.

Для реализации этого функционала мы будем использовать [широковещательный канал](https://docs.rs/tokio/latest/tokio/sync/broadcast/fn.channel.html) на сервере и [tokio_websockets](https://docs.rs/tokio-websockets/) для взаимодействия между клиентом и сервером.

Создайте новый проект и добавьте следующие зависимости в `Cargo.toml`:

```toml
[package]
name = "chat-async"
version = "0.1.0"
edition = "2021"

[dependencies]
futures-util = { version = "0.3.30", features = ["sink"] }
http = "1.0.0"
tokio = { version = "1.28.1", features = ["full"] }
tokio-websockets = { version = "0.5.1", features = ["client", "fastrand", "server", "sha1_smol"] }
```

_Необходимые API_

Вам потребуются следующие функции из `tokio` и `tokio_websockets`. Потратьте несколько минут для ознакомления со следующими API:

- [StreamExt::next()](https://docs.rs/futures-util/0.3.28/futures_util/stream/trait.StreamExt.html#method.next), реализуемый `WebSocketStream` - для асинхронного чтения сообщений из потока веб-сокетов
- [SinkExt::send()](https://docs.rs/futures-util/0.3.28/futures_util/sink/trait.SinkExt.html#method.send), реализуемый `WebSocketStream` - для асинхронной отправки сообщений в поток веб-сокетов
- [Lines::next_line()](https://docs.rs/tokio/latest/tokio/io/struct.Lines.html#method.next_line) - для асинхронного чтения сообщений пользователя через стандартный ввод
- [Sender::subscribe()](https://docs.rs/tokio/latest/tokio/sync/broadcast/struct.Sender.html#method.subscribe) - для подписки на широковещательный канал

_Два бинарника_

Как правило, в проекте может быть только один исполняемый файл (binary) и один файл `src/main.rs`. Нам требуется два бинарника. Один для клиента и еще один для сервера. Теоретически их можно сделать двумя отдельными проектами, но мы поместим оба бинарника в один проект. Для того, чтобы это работало, клиент и сервер должны находиться в директории `src/bin` (см. [документацию](https://doc.rust-lang.org/cargo/reference/cargo-targets.html#binaries)).

Скопируйте следующий код сервера и клиента в `src/bin/server.rs` и `src/bin/client.rs`, соответственно.

```rust
// src/bin/server.rs
use futures_util::sink::SinkExt;
use futures_util::stream::StreamExt;
use std::error::Error;
use std::net::SocketAddr;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::broadcast::{channel, Sender};
use tokio_websockets::{Message, ServerBuilder, WebSocketStream};

async fn handle_connection(
    addr: SocketAddr,
    mut ws_stream: WebSocketStream<TcpStream>,
    bcast_tx: Sender<String>,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    todo!("реализуй меня")
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    let (bcast_tx, _) = channel(16);

    let listener = TcpListener::bind("127.0.0.1:2000").await?;
    println!("Запросы принимаются на порту 2000");

    loop {
        let (socket, addr) = listener.accept().await?;
        println!("Запрос от {addr:?}");
        let bcast_tx = bcast_tx.clone();
        tokio::spawn(async move {
            // Оборачиваем сырой поток TCP в веб-сокет
            let ws_stream = ServerBuilder::new().accept(socket).await?;

            handle_connection(addr, ws_stream, bcast_tx).await
        });
    }
}
```

```rust
// src/bin/client.rs
use futures_util::stream::StreamExt;
use futures_util::SinkExt;
use http::Uri;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio_websockets::{ClientBuilder, Message};

#[tokio::main]
async fn main() -> Result<(), tokio_websockets::Error> {
    let (mut ws_stream, _) =
        ClientBuilder::from_uri(Uri::from_static("ws://127.0.0.1:2000"))
            .connect()
            .await?;

    let stdin = tokio::io::stdin();
    let mut stdin = BufReader::new(stdin).lines();

    todo!("реализуй меня")
}
```

_Запуск бинарников_

Команда для запуска сервера:

```bash
cargo run --bin server
```

Команда для запуска клиента:

```bash
cargo run --bin client
```

_Задачи_

- реализовать функцию `handle_connection` в `src/bin/server.rs`
  - подсказка: используйте `tokio::select!` для параллельного выполнения двух задач в бесконечном цикле. Одна задача получает сообщения от клиента и передает их другим клиентам. Другая - отправляет клиенту сообщения, полученные от сервера
- завершите функцию `main` в `src/bin/client.rs`
  - подсказка: также используйте `tokio::select!` в бесконечном цикле для параллельного выполнения двух задач: 1) чтение сообщений пользователя из стандартного ввода и их отправка серверу; 2) получение сообщений от сервера и их отображение
- опционально: измените код для передачи сообщений всем клиентам, кроме отправителя

<details>
<summary>Решение:</summary>

```rust
// src/bin/server.rs
use futures_util::sink::SinkExt;
use futures_util::stream::StreamExt;
use std::error::Error;
use std::net::SocketAddr;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::broadcast::{channel, Sender};
use tokio_websockets::{Message, ServerBuilder, WebSocketStream};

async fn handle_connection(
    addr: SocketAddr,
    mut ws_stream: WebSocketStream<TcpStream>,
    bcast_tx: Sender<String>,
) -> Result<(), Box<dyn Error + Send + Sync>> {

    ws_stream
        .send(Message::text("Добро пожаловать в чат! Отправьте сообщение".to_string()))
        .await?;
    let mut bcast_rx = bcast_tx.subscribe();

    // Бесконечный цикл для параллельного выполнения двух задач:
    // 1) получение сообщений из `ws_stream` и их передача клиентам
    // 2) получение сообщений в `bcast_rx` и их отправка клиенту
    loop {
        tokio::select! {
            incoming = ws_stream.next() => {
                match incoming {
                    Some(Ok(msg)) => {
                        if let Some(text) = msg.as_text() {
                            println!("{addr:?}: {text:?}");
                            bcast_tx.send(text.into())?;
                        }
                    }
                    Some(Err(err)) => return Err(err.into()),
                    None => return Ok(()),
                }
            }
            msg = bcast_rx.recv() => {
                ws_stream.send(Message::text(msg?)).await?;
            }
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error + Send + Sync>> {
    let (bcast_tx, _) = channel(16);

    let listener = TcpListener::bind("127.0.0.1:2000").await?;
    println!("Запросы принимаются на порту 2000");

    loop {
        let (socket, addr) = listener.accept().await?;
        println!("Запрос от {addr:?}");
        let bcast_tx = bcast_tx.clone();
        tokio::spawn(async move {
            // Оборачиваем сырой поток TCP в веб-сокет
            let ws_stream = ServerBuilder::new().accept(socket).await?;

            handle_connection(addr, ws_stream, bcast_tx).await
        });
    }
}
```

```rust
// src/bin/client.rs
use futures_util::stream::StreamExt;
use futures_util::SinkExt;
use http::Uri;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio_websockets::{ClientBuilder, Message};

#[tokio::main]
async fn main() -> Result<(), tokio_websockets::Error> {
    let (mut ws_stream, _) =
        ClientBuilder::from_uri(Uri::from_static("ws://127.0.0.1:2000"))
            .connect()
            .await?;

    let stdin = tokio::io::stdin();
    let mut stdin = BufReader::new(stdin).lines();

    // Бесконечный цикл для параллельной отправки и получения сообщений
    loop {
        tokio::select! {
            incoming = ws_stream.next() => {
                match incoming {
                    Some(Ok(msg)) => {
                        if let Some(text) = msg.as_text() {
                            println!("От сервера: {}", text);
                        }
                    },
                    Some(Err(err)) => return Err(err.into()),
                    None => return Ok(()),
                }
            }
            res = stdin.next_line() => {
                match res {
                    Ok(None) => return Ok(()),
                    Ok(Some(line)) => ws_stream.send(Message::text(line.to_string())).await?,
                    Err(err) => return Err(err.into()),
                }
            }

        }
    }
}
```

</details>
