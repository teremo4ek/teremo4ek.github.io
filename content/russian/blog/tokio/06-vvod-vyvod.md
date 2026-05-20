---
title: "Ввод-вывод"
description: "AsyncRead, AsyncWrite, эхо-сервер, разделение читателя и писателя"
date: 2026-05-20T05:00:00Z
weight: 6
image: "/images/tokio/06-vvod-vyvod-cover.png"
categories: ["Rust"]
tags: ["rust", "tokio"]
---

Ввод-вывод в Tokio работает почти так же, как и в `std`, но асинхронно. Существует типаж для чтения ([AsyncRead](https://docs.rs/tokio/1/tokio/io/trait.AsyncRead.html)) и типаж для записи ([AsyncWrite](https://docs.rs/tokio/1/tokio/io/trait.AsyncWrite.html)). Определенные типы реализуют эти типажи соответствующим образом ([TcpStream](https://docs.rs/tokio/1/tokio/net/struct.TcpStream.html), [File](https://docs.rs/tokio/1/tokio/fs/struct.File.html), [Stdout](https://docs.rs/tokio/1/tokio/io/struct.Stdout.html)). `AsyncRead` и `AsyncWrite` также реализуются рядом структур данных, таких как `Vec<u8>` и `&[u8]`. Это позволяет использовать массивы байтов там, где ожидается читатель или писатель.

В этом разделе будут рассмотрены базовые операции чтения и записи с помощью Tokio, а также приведено несколько примеров. В следующем разделе будет рассмотрен более продвинутый пример обработки ввода-вывода.

## `AsyncRead` и `AsyncWrite`

Эти типажи предоставляют возможности асинхронного чтения и записи в потоки байтов. Методы этих типажей обычно не вызываются напрямую, подобно тому, как мы не вызываем вручную метод `call` типажа `Future`. Вместо этого, они используются через вспомогательные методы, предоставляемые [AsyncReadExt](https://docs.rs/tokio/1/tokio/io/trait.AsyncReadExt.html) и [AsyncWriteExt](https://docs.rs/tokio/1/tokio/io/trait.AsyncWriteExt.html).

Кратко рассмотрим некоторые из этих методов. Все эти функции являются асинхронными и должны использоваться с `.await`.

__`async fn read()`__

[AsyncReadExt::read](https://docs.rs/tokio/1/tokio/io/trait.AsyncReadExt.html#method.read) предоставляет асинхронный метод для чтения данных в буфер, возвращающий количество прочитанных байтов.

Если `read()` возвращает `Ok(0)`, это означает одно из двух:

1. Читатель достиг EOF и, вероятно, больше не сможет производить байты. _Обратите внимание_: это не означает, что читатель _никогда_ больше не сможет производить байты.
2. Длина указанного буфера составляет 0 байт.

Дальнейшие вызовы `read()` будут немедленно возвращать `Ok(0)`. Для экземпляров [TcpStream](https://docs.rs/tokio/1/tokio/net/struct.TcpStream.html) это означает, что половина сокета для чтения закрыта.

```rust
use tokio::fs::File;
use tokio::io::{self, AsyncReadExt};

#[tokio::main]
async fn main() -> io::Result<()> {
    let mut f = File::open("test.txt").await?;
    let mut buffer = [0; 10];

    // Читаем от 0 до 10 байтов
    f.read(&mut buffer[..]).await?;

    // Выводим в терминал первые 10 байтов
    println!("The bytes: {:?}", buffer);
    Ok(())
}
```

__`async fn read_to_end()`__

[AsyncReadExt::read_to_end](https://docs.rs/tokio/1/tokio/io/trait.AsyncReadExt.html#method.read_to_end) считывает все байты из потока до EOF:

```rust
use tokio::io::{self, AsyncReadExt};
use tokio::fs::File;

#[tokio::main]
async fn main() -> io::Result<()> {
    let mut f = File::open("test.txt").await?;
    let mut buffer = Vec::new();

    // Читаем весь файл
    f.read_to_end(&mut buffer).await?;

    // Выводим в терминал содержимое файла
    println!("{}", String::from_utf8_lossy(&buffer));
    Ok(())
}
```

__`async fn write()`__

[AsyncWriteExt::write](https://docs.rs/tokio/1/tokio/io/trait.AsyncWriteExt.html#method.write) записывает буфер в файл, возвращая количество записанных байтов:

```rust
use tokio::fs::File;
use tokio::io::{self, AsyncWriteExt};

#[tokio::main]
async fn main() -> io::Result<()> {
    let mut file = File::create("test.txt").await?;

    // Записываем часть байтовой строки в файл
    let n = file.write(b"some bytes").await?;

    // Выводим в терминал количество записанных байтов
    println!("Wrote the first {} bytes of 'some bytes'.", n);
    Ok(())
}
```

__`async fn write_all()`__

[AsyncWriteExt::write_all](https://docs.rs/tokio/1/tokio/io/trait.AsyncWriteExt.html#method.write_all) записывает весь буфер в файл:

```rust
use tokio::fs::File;
use tokio::io::{self, AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn main() -> io::Result<()> {
    // Создаем или открываем файл для записи
    let mut file = File::create("test.txt").await?;

    // Записываем байтовую строку в файл
    file.write_all(b"some bytes").await?;

    // Открываем файл для чтения
    file = File::open("test.txt").await?;
    let mut buffer = Vec::new();

    // Читаем байты из файла
    file.read_to_end(&mut buffer).await?;

    // Выводим в терминал содержимое файла
    println!("{}", String::from_utf8_lossy(&buffer));
    Ok(())
}
```

## Вспомогательные функции

Как и `std`, модуль [tokio::io](https://docs.rs/tokio/1/tokio/io/index.html) содержит ряд полезных утилит, а также API для работы со [стандартным вводом](https://docs.rs/tokio/1/tokio/io/fn.stdin.html), [стандартным выводом](https://docs.rs/tokio/1/tokio/io/fn.stdout.html) и [стандартными ошибками](https://docs.rs/tokio/1/tokio/io/fn.stderr.html). Например, [tokio::io::copy](https://docs.rs/tokio/1/tokio/io/fn.copy.html) асинхронно копирует все содержимое устройства чтения в устройство записи:

```rust
use tokio::fs::File;
use tokio::io;

#[tokio::main]
async fn main() -> io::Result<()> {
    let mut reader: &[u8] = b"hello";
    let mut file = File::create("test.txt").await?;

    io::copy(&mut reader, &mut file).await?;
    Ok(())
}
```

_Обратите внимание_, здесь используется то, что байтовые массивы также реализуют `AsyncRead`.

## Эхо-сервер

Поупражняемся в работе с асинхронным вводом-выводом. Напишем эхо-сервер.

Эхо-сервер "привязывает" `TcpListener` и принимает входящие соединения в цикле. Для каждого входящего соединения данные считываются из сокета и немедленно записываются обратно в него. Клиент отправляет данные на сервер и получает их обратно.

Мы реализуем эхо-сервер дважды с помощью разных стратегий.

__`io::copy()`__

Начнем с реализации сервера с помощью утилиты [io::copy](https://docs.rs/tokio/1/tokio/io/fn.copy.html).

Создаем новый двоичный файл:

```bash
touch src/bin/echo-server-copy.rs
```

Команда для запуска примера:

```bash
cargo run --bin echo-server-copy
```

Тестировать сервер можно, используя стандартный инструмент командной строки, такой как `telnet`, или написав простой клиент, подобный тому, который можно найти в документации [tokio::net::TcpStream](https://docs.rs/tokio/1/tokio/net/struct.TcpStream.html#examples).

Это TCP-сервер, и ему нужен цикл принятия. Для обработки каждого входящего сокета создается новая задача.

```rust
use tokio::io;
use tokio::net::TcpListener;

#[tokio::main]
async fn main() -> io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:6142").await?;

    loop {
        let (mut socket, _) = listener.accept().await?;

        tokio::spawn(async move {
            // Копируем данные
        });
    }
}
```

Эта утилита берет устройства чтения и записи и копирует данные из одного в другой. Однако у нас есть только один `TcpStream`. Он реализует как `AsyncRead`, так и `AsyncWrite`. Поскольку `io::copy` требует `&mut` как для чтения, так и для записи, сокет нельзя использовать для обоих аргументов.

```rust
// Это не будет компилироваться
io::copy(&mut socket, &mut socket).await
```

__Разделение читателя и писателя__

Для решения этой проблемы, мы должны разделить сокет на дескриптор чтения и дескриптор записи. Лучший способ это сделать зависит от конкретного типа.

Любой тип `читатель + писатель` можно разделить с помощью утилиты [io::split](https://docs.rs/tokio/1/tokio/io/fn.split.html). Эта функция принимает одно значение и возвращает отдельные дескрипторы чтения и записи. Эти два дескриптора можно использовать независимо, в том числе, в отдельных задачах.

Например, эхо-клиент может обрабатывать одновременные операции чтения и записи следующим образом:

```rust
use tokio::io::{self, AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

#[tokio::main]
async fn main() -> io::Result<()> {
    let socket = TcpStream::connect("127.0.0.1:6142").await?;
    let (mut rd, mut wr) = io::split(socket);

    // Записываем данные в фоновом режиме
    tokio::spawn(async move {
        wr.write_all(b"hello\r\n").await?;
        wr.write_all(b"world\r\n").await?;

        // Иногда компилятору Rust нужна небольшая помощь
        // для вывода правильного типа
        Ok::<_, io::Error>(())
    });

    let mut buf = vec![0; 128];

    loop {
        let n = rd.read(&mut buf).await?;

        if n == 0 {
            break;
        }

        println!("GOT {:?}", &buf[..n]);
    }

    Ok(())
}
```

Поскольку `io::split()` поддерживает любое значение, реализующее `AsyncRead` + `AsyncWrite`, и возвращает независимые дескрипторы, внутри `io::split()` используются `Arc` и `Mutex`. Этих накладных расходов можно избежать с помощью `TcpStream`, который предоставляет две функции разделения.

[TcpStream::split](https://docs.rs/tokio/1/tokio/net/struct.TcpStream.html#method.split) принимает ссылку на поток и возвращает дескрипторы чтения и записи. Поскольку используется ссылка, оба дескриптора должны оставаться в той же задаче, из которой вызывается `split()`. Эта функция является бесплатной. `Arc` или `Mutex` ей не нужны. `TcpStream` также предоставляет функцию [into_split](https://docs.rs/tokio/1/tokio/net/struct.TcpStream.html#method.into_split), возвращающую дескрипторы, которые могут перемещаться между задачами за счет только `Arc`.

Поскольку `io::copy()` вызывается для задачи, которая владеет `TcpStream`, мы можем использовать `TcpStream::split()`. Задача, отвечающая за логику на сервере, будет выглядеть так:

```rust
tokio::spawn(async move {
    let (mut rd, mut wr) = socket.split();

    if io::copy(&mut rd, &mut wr).await.is_err() {
        eprintln!("Failed to copy");
    }
});
```

Полный код примера можно найти [здесь](https://github.com/tokio-rs/website/blob/master/tutorial-code/io/src/echo-server-copy.rs).

__Ручное копирование__

Теперь посмотрим на эхо-сервер, копирующий данные вручную. Для этого мы будем использовать [AsyncReadExt::read](https://docs.rs/tokio/1/tokio/io/trait.AsyncReadExt.html#method.read) и [AsyncWriteExt::write_all](https://docs.rs/tokio/1/tokio/io/trait.AsyncWriteExt.html#method.write_all).

Полный код сервера:

```rust
use tokio::io::{self, AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

#[tokio::main]
async fn main() -> io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:6142").await?;

    loop {
        let (mut socket, _) = listener.accept().await?;

        tokio::spawn(async move {
            let mut buf = vec![0; 1024];

            loop {
                match socket.read(&mut buf).await {
                    // `Ok(0)` свидетельствует о закрытии сокета
                    Ok(0) => return,
                    Ok(n) => {
                        // Копируем данные обратно в сокет
                        if socket.write_all(&buf[..n]).await.is_err() {
                            // Неожиданная ошибка сокета. Мы ничего не можем с ней сделать,
                            // так что просто прекращаем обработку
                            return;
                        }
                    }
                    Err(_) => {
                        // Неожиданная ошибка сокета
                        return;
                    }
                }
            }
        });
    }
}
```

Этот код можно поместить в `src/bin/echo-server.rs` и запустить с помощью `cargo run --bin echo-server`.

Разберем код построчно. Во-первых, поскольку используются утилиты `AsyncRead` и `AsyncWrite`, в область видимости должны быть включены расширяющие их типажи:

```rust
use tokio::io::{self, AsyncReadExt, AsyncWriteExt};
```

__Выделение буфера__

Стратегия состоит в том, чтобы прочитать данные из сокета в буфер, а затем записать содержимое буфера обратно в сокет:

```rust
let mut buf = vec![0; 1024];
```

Мы специально не используем стековый буфер. Ранее мы отмечали, что все данные задачи, которые сохраняются при вызовах `.await`, должны храниться в задаче. В этом случае `buf` используется при вызовах `.await`. Все данные задачи хранятся в одном месте. Об этом можно думать как о `enum`, где каждый вариант - это данные, которые необходимо сохранить для конкретного вызова `.await`.

Если буфер представлен массивом стека, внутренняя структура задач, создаваемых для каждого принятого сокета, может выглядеть примерно так:

```rust
struct Task {
    // Внутренние поля задачи
    task: enum {
        AwaitingRead {
            socket: TcpStream,
            buf: [BufferType],
        },
        AwaitingWriteAll {
            socket: TcpStream,
            buf: [BufferType],
        }

    }
}
```

Если в качестве типа буфера используется стековый массив, он будет храниться внутри структуры задачи. Это сделает структуру задачи очень большой. Кроме того, размеры буфера часто соответствуют размеру страницы. Это, в свою очередь, приведет к неуклюжему размеру `Task`: `$page-size + несколько-байт`.

На самом деле компилятор использует более оптимальное представление состояния асинхронного блока, чем простой `enum`. На практике переменные не перемещаются между вариантами, как это требуется при перечислении. Однако размер структуры задачи по крайней мере равен размеру самой большой переменной.

По этой причине обычно более эффективно использовать отдельное пространство для буфера.

__Обработка EOF__

Когда читатель `TCPStream` закрывается, вызов `read()` возвращает `Ok(0)`. На этом этапе важно выйти из цикла чтения. Забывание об этом является распространенным источником ошибок.

```rust
loop {
    match socket.read(&mut buf).await {
        Ok(0) => return,
        // ...
    }
}
```

Полный код примера можно найти [здесь](https://github.com/tokio-rs/website/blob/master/tutorial-code/io/src/echo-server.rs).

---
