---
title: "Создание задач"
description: "TcpListener, tokio::spawn, задачи, привязка 'static и Send, хранение значений"
date: 2026-05-20T05:00:00Z
weight: 3
image: "/images/tokio/03-sozdanie-potokov-cover.png"
categories: ["Rust"]
tags: ["rust", "tokio"]
---

## Создание потоков

Приступим к разработке сервера Redis.

Сначала переместим код клиента из предыдущего раздела в отдельный файл:

```bash
mkdir -p examples
mv src/main.rs examples/hello-redis.rs
```

Затем создадим новый пустой файл `src/main.rs`.

### Прием сокетов

Первое, что должен делать наш сервер, - принимать входящие TCP-сокеты. Это делается путем привязки [tokio::net::TcpListener](https://docs.rs/tokio/1/tokio/net/struct.TcpListener.html) к порту _6379_.

> Многие типы Tokio называются также, как их синхронные эквиваленты в стандартной библиотеке Rust. Когда это имеет смысл, Tokio предоставляет те же API, что и `std`, но с использованием `async fn`.

Сокеты принимаются в цикле. Каждый сокет обрабатывается и закрывается. Прочитаем команду, выведем ее на стандартный вывод и ответим ошибкой:

```rust
// src/main.rs
use tokio::net::{TcpListener, TcpStream};
use mini_redis::{Connection, Frame};

#[tokio::main]
async fn main() {
    // Привязываем обработчик к адресу
    let listener = TcpListener::bind("127.0.0.1:6379").await.unwrap();

    loop {
        // Второй элемент содержит IP и порт нового подключения
        let (socket, _) = listener.accept().await.unwrap();
        process(socket).await;
    }
}

async fn process(socket: TcpStream) {
    // `Connection` позволяет читать/писать кадры (frames) redis вместо
    // потоков байтов. Тип `Connection` определяется mini-redis
    let mut connection = Connection::new(socket);

    if let Some(frame) = connection.read_frame().await.unwrap() {
        println!("GOT: {:?}", frame);

        // Отвечаем ошибкой
        let response = Frame::Error("Unimplemented".to_string());
        connection.write_frame(&response).await.unwrap();
    }
}
```

Запускаем программу:

```bash
cargo run
```

Запускаем пример `hello-redis` в отдельном терминале:

```bash
cargo run --example hello-redis
```

Вывод в терминале примера:

```bash
Error: "Unimplemented"
```

Вывод в терминале сервера:

```bash
GOT: Array([Bulk(b"set"), Bulk(b"hello"), Bulk(b"world")])
```

### Одновременность

У нашего сервера есть небольшая проблема (помимо того, что он отвечает только ошибками). Он обрабатывает входящие запросы по одному. После установки соединения, сервер остается внутри цикла приема подключений до тех пор, пока ответ не будет полностью записан в сокет.

Мы хотим, чтобы наш сервер обрабатывал много запросов одновременно. Для этого нам нужно добавить немного конкурентности.

> Одновременность (concurrency) и параллелизм (parallelism) - это не одно и тоже. Если мы переключаемся между двумя задачами, то мы работаем над ними одновременно, а не параллельно. Чтобы эту работу можно было считать параллельной, нам потребуются два человека, по одному на каждую задачу.
>
> Одним из преимуществ использования Tokio является то, что асинхронный код позволяет работать над многими задачами одновременно, без необходимости работать над ними параллельно с использованием обычных потоков. Фактически, Tokio может выполнять множество задач одновременно в одном потоке!

Для одновременной обработки соединений для каждого входящего соединения создается новая задача. Соединение обрабатывается этой задачей.

Цикл принятия соединений становится таким:

```rust
use tokio::net::TcpListener;

#[tokio::main]
async fn main() {
    let listener = TcpListener::bind("127.0.0.1:6379").await.unwrap();

    loop {
        let (socket, _) = listener.accept().await.unwrap();
        // Для каждого входящего сокета создается новая задача. Сокет
        // перемещается в новую задачу и обрабатывается там
        tokio::spawn(async move {
            process(socket).await;
        });
    }
}
```

__Задачи__

Задача Tokio - это асинхронный зеленый поток (green thread). Они создаются путем передачи `async` блока в `tokio::spawn()`. Функция `tokio::spawn` возвращает `JoinHandle`, который вызывающая сторона может использовать для взаимодействия с созданной задачей. `async` блок может иметь возвращаемое значение. Вызывающая сторона может получить его с помощью `.await` на `JoinHandle`.

Например:

```rust
#[tokio::main]
async fn main() {
    let handle = tokio::spawn(async {
        // Выполняем асинхронную работу
        "return value"
    });

    // Выполняем другую работу

    let out = handle.await.unwrap();
    println!("GOT: {}", out);
}
```

Ожидание `JoinHandle` возвращает `Result`. Если во время выполнения задачи возникает ошибка, `JoinHandle` возвращает `Err`. Это происходит, когда задача либо вызывает панику, либо принудительно отменяется из-за закрытия среды выполнения.

Задача - это единица выполнения (unit of execution), управляемая планировщиком. При создании задачи она передается планировщику Tokio, который гарантирует ее выполнение при появлении у нее работы. Порожденная задача может выполняться в том же потоке, в котором она была создана, или в другом потоке времени выполнения. Задачу также можно перемещать между потоками после создания.

Задачи в Токио очень легкие. По сути, им требуется только одно выделение и 64 байта памяти. Приложения должны иметь возможность свободно создавать тысячи, если не миллионы задач.

__Привязка `'static`__

При создании задачи в среде выполнения Tokio, время жизни ее типа должно быть `'static`. Это означает, что порожденная задача не должна содержать никаких ссылок на данные, не принадлежащие ей.

> Распространено заблуждение, что `'static` означает "жить вечно", но это не так. Тот факт, что значение является `'static`, не означает, что у нас есть утечка памяти. Больше об этом можно прочитать [здесь](https://github.com/pretzelhammer/rust-blog/blob/master/posts/common-rust-lifetime-misconceptions.md#2-if-t-static-then-t-must-be-valid-for-the-entire-program).

Например, следующий код не скомпилируется:

```rust
use tokio::task;

#[tokio::main]
async fn main() {
    let v = vec![1, 2, 3];

    task::spawn(async {
        println!("Это вектор: {:?}", v);
    });
}
```

```bash
error[E0373]: async block may outlive the current function, but
              it borrows `v`, which is owned by the current function
 --> src/main.rs:7:23
  |
7 |       task::spawn(async {
  |  _______________________^
8 | |         println!("Это вектор: {:?}", v);
  | |                                      - `v` is borrowed here
9 | |     });
  | |_____^ may outlive borrowed value `v`
  |
note: function requires argument type to outlive `'static`
 --> src/main.rs:7:17
  |
7 |       task::spawn(async {
  |  _________________^
8 | |         println!("Это вектор: {:?}", v);
9 | |     });
  | |_____^
help: to force the async block to take ownership of `v` (and any other
      referenced variables), use the `move` keyword
  |
7 |     task::spawn(async move {
8 |         println!("Это вектор: {:?}", v);
9 |     });
  |
```

Это происходит потому, что по умолчанию переменные не перемещаются в асинхронные блоки. Вектор `v` остается во владении функции `main`. `println!` заимствует `v`. Компилятор Rust любезно объясняет нам это и даже предлагает исправление! Изменение строки 7 на `task::spawn(async move {` даст указание компилятору переместить `v` в порожденную задачу. Теперь задача владеет всеми своими данными, что делает их `'static`.

Если часть данных должна быть доступна одновременно в нескольких задачах, ее необходимо распределять (сделать общей) с помощью примитивов синхронизации, таких как `Arc`.

_Обратите внимание_, что в сообщении об ошибке говорится о том, что тип аргумента переживает время жизни `'static`. Эта терминология может сбивать с толку, поскольку время жизни `'static` длится до конца программы, поэтому, если тип переживает его, не возникает ли у нас утечки памяти? Объяснение состоит в том, что именно тип, а не значение, должен переживать время жизни `'static`, и значение может быть уничтожено до того, как его тип перестанет быть действительным.

Когда мы говорим, что значение является "статическим", это означает лишь то, что было бы правильно хранить его вечно. Это важно, поскольку компилятор не может определить, как долго будет выполняться вновь созданная задача. Мы должны убедиться, что задаче разрешено жить вечно, чтобы Tokio мог выполнять ее столько, сколько необходимо.

"Привязка `'static`", "тип, переживающий `'static`" и "`'static` значение" обозначают одно и тоже - `T: 'static`, в отличие от "аннотации с помощью `'static`", как в `&'static T`.

__Привязка `bound`__

Задачи, порожденные `tokio::spawn()`, должны реализовывать типаж `Send`. Это позволяет среде выполнения Tokio перемещать задачи между потоками, пока они приостановлены в `.await`.

Задачи являются `Send`, когда все данные, хранящиеся в вызовах `.await`, являются таковыми. При вызове `.await` задача возвращается (yields back) планировщику. При следующем выполнении задачи, она возобновляется с той точки, на которой была приостановлена (yielded) в последний раз. Чтобы это работало, все состояние, используемое после `.await`, должно сохраняться задачей. Если это состояние являются `Send`, т.е. его можно перемещать между потоками, то и саму задачу можно перемещать между потоками. И наоборот, если состояние не являются `Send`, то и задача тоже.

Например, это работает:

```rust
use tokio::task::yield_now;
use std::rc::Rc;

#[tokio::main]
async fn main() {
    tokio::spawn(async {
        // Область видимости уничтожает `rc` перед `.await`
        {
            let rc = Rc::new("hello");
            println!("{}", rc);
        }

        // `rc` больше не используется. Он не сохраняется, когда
        // задача возвращается планировщику
        yield_now().await;
    });
}
```

А это не работает:

```rust
use tokio::task::yield_now;
use std::rc::Rc;

#[tokio::main]
async fn main() {
    tokio::spawn(async {
        let rc = Rc::new("hello");

        // `rc` используется после `.await`. Он должен быть сохранен в
        // состоянии задачи
        yield_now().await;

        println!("{}", rc);
    });
}
```

Попытка компиляции этого фрагмента завершается такой ошибкой:

```bash
error: future cannot be sent between threads safely
   --> src/main.rs:6:5
    |
6   |     tokio::spawn(async {
    |     ^^^^^^^^^^^^ future created by async block is not `Send`
    |
   ::: [..]spawn.rs:127:21
    |
127 |         T: Future + Send + 'static,
    |                     ---- required by this bound in
    |                          `tokio::task::spawn::spawn`
    |
    = help: within `impl std::future::Future`, the trait
    |       `std::marker::Send` is not  implemented for
    |       `std::rc::Rc<&str>`
note: future is not `Send` as this value is used across an await
   --> src/main.rs:10:9
    |
7   |         let rc = Rc::new("hello");
    |             -- has type `std::rc::Rc<&str>` which is not `Send`
...
10  |         yield_now().await;
    |         ^^^^^^^^^^^^^^^^^ await occurs here, with `rc` maybe
    |                           used later
11  |         println!("{}", rc);
12  |     });
    |     - `rc` is later dropped here
```

### Хранение значений

Теперь мы реализуем функцию `process` для обработки входящих команд. Мы будем использовать `HashMap` для хранения значений. Команды `SET` будут добавлять значения в `HashMap`, а команды `GET` будут извлекать значения из `HashMap`. Кроме того, мы будем использовать цикл для приема нескольких команд в одном соединении.

```rust
use tokio::net::TcpStream;
use mini_redis::{Connection, Frame};

async fn process(socket: TcpStream) {
    use mini_redis::Command::{self, Get, Set};
    use std::collections::HashMap;

    // Хранилище данных
    let mut db = HashMap::new();

    // `Connection`, предоставляемое `mini-redis`, обрабатывает разбор кадров из сокета
    let mut connection = Connection::new(socket);

    // Используем `read_frame` для получения команды из соединения
    while let Some(frame) = connection.read_frame().await.unwrap() {
        let response = match Command::from_frame(frame).unwrap() {
            Set(cmd) => {
                // Значение хранится в виде `Vec<u8>`
                db.insert(cmd.key().to_string(), cmd.value().to_vec());
                Frame::Simple("OK".to_string())
            }
            Get(cmd) => {
                if let Some(value) = db.get(cmd.key()) {
                    // `Frame::Bulk` ожидает, что данные будут иметь тип `Bytes`.
                    // Мы рассмотрим этот тип позже.
                    // `&Vec<u8>` преобразуется в `Bytes` с помощью метода `into`
                    Frame::Bulk(value.clone().into())
                } else {
                    Frame::Null
                }
            }
            cmd => panic!("Не реализовано {:?}", cmd),
        };

        // Отправляем (пишем) ответ клиенту
        connection.write_frame(&response).await.unwrap();
    }
}
```

Запускаем сервер:

```bash
cargo run
```

В отдельном терминале запускаем пример `hello-redis`:

```bash
cargo run --example hello-redis
```

Полный код примера можно найти [здесь](https://github.com/tokio-rs/website/blob/master/tutorial-code/spawning/src/main.rs).

Теперь мы можем устанавливать и получать значения, но есть одна проблема: значения не распределяются между соединениями. Если другой подключенный сокет попытается получить значение по ключу `hello`, он получит `(nil)`.
