---
title: "Кадрирование"
description: "Уровень кадрирования: буферизованное чтение, разбор кадров и буферизованная запись"
date: 2026-05-20T05:00:00Z
weight: 7
image: "/images/tokio/07-kadrirovanie-cover.png"
categories: ["Rust"]
tags: ["rust", "tokio"]
---

Применим то, что мы узнали о вводе-выводе, и реализуем уровень кадрирования (framing layer) Mini-Redis. Кадрирование (framing) - это процесс получения потока байтов и преобразования его в поток кадров. Кадр - это единица данных, передаваемая между двумя узлами (peers). Кадр протокола Redis определяется следующим образом:

```rust
use bytes::Bytes;

enum Frame {
    Simple(String),
    Error(String),
    Integer(u64),
    Bulk(Bytes),
    Null,
    Array(Vec<Frame>),
}
```

_Обратите внимание_, что кадр состоит только из данных без какой-либо семантики. Анализ и реализация команд происходят на более высоком уровне.

Для HTTP кадр может выглядеть так:

```rust
enum HttpFrame {
    RequestHead {
        method: Method,
        uri: Uri,
        version: Version,
        headers: HeaderMap,
    },
    ResponseHead {
        status: StatusCode,
        version: Version,
        headers: HeaderMap,
    },
    BodyChunk {
        chunk: Bytes,
    },
}
```

Реализуем структуру `Connection`, которая оборачивает `TcpStream` и читает/записывает значения `mini_redis::Frame`:

```rust
use tokio::net::TcpStream;
use mini_redis::{Frame, Result};

struct Connection {
    stream: TcpStream,
    // ...
}

impl Connection {
    /// Читает кадр из соединения.
    ///
    /// Возвращает `None` при достижении EOF
    pub async fn read_frame(&mut self)
        -> Result<Option<Frame>>
    {
        // TODO
    }

    /// Записывает кадр в соединение
    pub async fn write_frame(&mut self, frame: &Frame)
        -> Result<()>
    {
        // TODO
    }
}
```

Подробную информацию о протоколе Redis можно найти [здесь](https://redis.io/topics/protocol). Полный код `Connection` можно найти [здесь](https://github.com/tokio-rs/mini-redis/blob/tutorial/src/connection.rs).

## Буферизованное чтение

Метод `read_frame` ожидает получения всего кадра перед возвратом. Один вызов `TcpStream::read()` может вернуть произвольный объем данных. Он может содержать целый кадр, часть кадра или несколько кадров. Если получен частичный кадр, данные буферизуются, и из сокета считываются дополнительные данные. Если получено несколько кадров, возвращается первый, а остальные данные помещаются в буфер до следующего вызова `read_frame()`.

Создаем новый файл:

```bash
touch src/connection.rs
```

Далее в `Connection` нужно добавить поле для буфера чтения (read buffer). Данные считываются из сокета в буфер чтения. При разборе кадра соответствующие данные удаляются из буфера.

Мы будем использовать [BytesMut](https://docs.rs/bytes/1/bytes/struct.BytesMut.html) в качестве типа буфера. Это изменяемая версия [Bytes](https://docs.rs/bytes/1/bytes/struct.Bytes.html).

```rust
use bytes::BytesMut;
use tokio::net::TcpStream;

pub struct Connection {
    stream: TcpStream,
    buffer: BytesMut,
}

impl Connection {
    pub fn new(stream: TcpStream) -> Connection {
        Connection {
            stream,
            // Выделяем буфер размером 4 КБ
            buffer: BytesMut::with_capacity(4096),
        }
    }
}
```

Реализуем метод `read_frame`:

```rust
use tokio::io::AsyncReadExt;
use bytes::Buf;
use mini_redis::Result;

pub async fn read_frame(&mut self)
    -> Result<Option<Frame>>
{
    loop {
        // Пытаемся разобрать кадр из буферизованных данных.
        // Если данных в буфере достаточно, возвращается кадр
        if let Some(frame) = self.parse_frame()? {
            return Ok(Some(frame));
        }

        // В буфере недостаточно данных для чтения кадра.
        // Пытаемся получить больше данных из сокета.
        //
        // При успехе возвращается количество байтов.
        // `0` - индикатор "конца потока"
        if 0 == self.stream.read_buf(&mut self.buffer).await? {
            // Другая сторона закрыла соединение. Для чистого закрытия
            // в буфере чтения не должно оставаться данных.
            // Если такие данные имеются, значит другая сторона
            // закрыла соединение во время передачи кадра
            if self.buffer.is_empty() {
                return Ok(None);
            } else {
                return Err("Connection reset by peer".into());
            }
        }
    }
}
```

Разберем этот код. Метод `read_frame` работает в цикле. Сначала вызывается `self.parse_frame()`. Этот метод пытается разобрать кадр Redis из `self.buffer`. Если данных достаточно, кадр возвращается вызывающей стороне. В противном случае, мы пытаемся прочитать больше данных из сокета. После считывания дополнительных данных снова вызывается `parse_frame()`.

При чтении из потока возвращаемое значение `0` указывает, что данных от узла больше не будет. Если в буфере чтения все еще есть данные, это означает, что был получен частичный кадр и соединение прервано внезапно. Это состояние ошибки, поэтому возвращается `Err`.

__Типаж `Buf`__

При чтении из потока вызывается `read_buf()`. Эта версия функции чтения принимает значение, реализующее [BufMut](https://docs.rs/bytes/1/bytes/trait.BufMut.html) из крейта [bytes](https://docs.rs/bytes/).

Во-первых, подумайте, как мы могли бы реализовать тот же цикл чтения, используя `read()`. Вместо `BytesMut` можно использовать `Vec<u8>`:

```rust
use tokio::net::TcpStream;

pub struct Connection {
    stream: TcpStream,
    buffer: Vec<u8>,
    cursor: usize,
}

impl Connection {
    pub fn new(stream: TcpStream) -> Connection {
        Connection {
            stream,
            buffer: vec![0; 4096],
            cursor: 0,
        }
    }
}
```

Функция `read_frame` в `Connection`:

```rust
use mini_redis::{Frame, Result};

pub async fn read_frame(&mut self)
    -> Result<Option<Frame>>
{
    loop {
        if let Some(frame) = self.parse_frame()? {
            return Ok(Some(frame));
        }

        // Проверяем наличие свободного места в буфере
        if self.buffer.len() == self.cursor {
            // Увеличиваем размер буфера
            self.buffer.resize(self.cursor * 2, 0);
        }

        // Читаем в буфер, отслеживая количество прочитанных байт
        let n = self.stream.read(&mut self.buffer[self.cursor..]).await?;

        if 0 == n {
            if self.cursor == 0 {
                return Ok(None);
            } else {
                return Err("Connection reset by peer".into());
            }
        } else {
            // Обновляем курсор
            self.cursor += n;
        }
    }
}
```

При работе с байтовыми массивами и `read()`, мы должны поддерживать курсор, отслеживающий, какой объем данных был помещен в буфер. Мы должны обязательно передать в функцию `read` пустую часть буфера. В противном случае, мы перезапишем буферизованные данные. Если буфер заполняется, мы должны увеличить его, чтобы продолжить чтение. В `parse_frame()` (не входит в пример) нам нужно будет проанализировать данные, содержащиеся в `self.buffer[..self.cursor]`.

Поскольку соединение массива байтов с курсором является очень распространенным, крейт `bytes` предоставляет абстракцию, представляющую массив байтов и курсор. Типаж `Buf` реализуется типами, из которых можно читать данные. Типаж `BufMut` реализуется типами, в которые можно записывать данные. При передаче `T: BufMut` в `read_buf()` внутренний курсор буфера автоматически обновляется. Благодаря этому в нашей версии `read_frame()` нам не нужно управлять собственным курсором.

Кроме того, при использовании `Vec<u8>` буфер необходимо инициализировать. `vec![0; 4096]` выделяет массив размером 4096 байт и записывает ноль в каждую ячейку. При изменении размера буфера новая емкость также должна быть инициализирована нулями. Процесс инициализации не является бесплатным. При работе с `BytesMut` и `BufMut` емкость не инициализируется. Абстракция `BytesMut` не позволяет нам читать неинициализированную память. Это позволяет нам избежать этапа инициализации.

## Разбор

Теперь рассмотрим функцию `parse_frame`. Разбор выполняется в два этапа:

1. Убеждаемся, что в буфере находится полный кадр, и находим конечный индекс кадра.
2. Разбираем кадр.

Крейт mini-redis предоставляет нам функции для обоих этих шагов:

1. [Frame::check](https://docs.rs/mini-redis/0.4/mini_redis/frame/enum.Frame.html#method.check).
2. [Frame::parse](https://docs.rs/mini-redis/0.4/mini_redis/frame/enum.Frame.html#method.parse).

Мы также будем повторно использовать абстракцию `Buf`. `Buf` передается в `Frame::check()`. Поскольку функция `check` перебирает переданный буфер, внутренний курсор перемещается вперед. Когда `check()` возвращается, внутренний курсор буфера указывает на конец кадра.

Для типа `Buf` мы будем использовать `std::io::Cursor<&[u8]>`:

```rust
use mini_redis::{Frame, Result};
use mini_redis::frame::Error::Incomplete;
use bytes::Buf;
use std::io::Cursor;

fn parse_frame(&mut self)
    -> Result<Option<Frame>>
{
    // Создаем тип `T: Buf`
    let mut buf = Cursor::new(&self.buffer[..]);

    // Проверяем, доступен ли целый кадр
    match Frame::check(&mut buf) {
        Ok(_) => {
            // Получаем длину кадра в байтах
            let len = buf.position() as usize;

            // Сбрасываем внутренний курсор для вызова `parse()`
            buf.set_position(0);

            // Разбираем кадр
            let frame = Frame::parse(&mut buf)?;

            // Удаляем кадр из буфера
            self.buffer.advance(len);

            // Возвращаем кадр
            Ok(Some(frame))
        }
        // В буфере содержится мало данных
        Err(Incomplete) => Ok(None),
        // Возникла ошибка
        Err(e) => Err(e.into()),
    }
}
```

Полный код функции `Frame::check` можно найти [здесь](https://github.com/tokio-rs/mini-redis/blob/tutorial/src/frame.rs#L65-L103).

Важно отметить, что используются API `Buf` в стиле "байтового итератора" (byte iterator). Речь идет об извлечении данных и перемещении внутреннего курсора. Например, чтобы определить тип кадра при его анализе, проверяется первый байт. Используемая функция - [Buf::get_u8](https://docs.rs/bytes/1/bytes/buf/trait.Buf.html#method.get_u8). Извлекается байт в текущей позиции курсора и курсор перемещается на единицу.

Типаж [Buf](https://docs.rs/bytes/1/bytes/buf/trait.Buf.html) предоставляет много полезных методов.

## Буферизованная запись

Другая половина API кадрирования - это функция `write_frame(frame)`. Эта функция записывает в сокет весь кадр. Чтобы свести к минимуму системные вызовы `write()`, запись буферизуется. Кадры кодируются в буфер записи (write buffer) перед записью в сокет. Однако, в отличие от `read_frame()`, весь кадр не всегда буферизуется в массив байтов перед записью в сокет.

Рассмотрим кадр массового (группового) потока (bulk stream frame). Записываемое значение - `Frame::Bulk(Bytes)`. Формат передачи группового кадра - это заголовок кадра, который состоит из символа `$`, за которым следует длина данных в байтах. Большую часть кадра составляет содержимое значения `Bytes`. Если данные большие, копирование их в промежуточный буфер будет дорогостоящим.

Для реализации буферизованной записи мы будем использовать структуру [BufWriter](https://docs.rs/tokio/1/tokio/io/struct.BufWriter.html). Эта структура инициализируется с помощью `T: AsyncWrite` и сама реализует `AsyncWrite`. При вызове `write()` в `BufWriter`, запись идет не непосредственно в файл для записи, а в буфер. Когда буфер заполняется, его содержимое сбрасывается во внутренний файл для записи, и буфер очищается. Также существуют оптимизации, позволяющие обходить (bypass) буфер в определенных случаях.

Мы реализуем только часть функции `write_frame`. Полную реализацию смотрите [здесь](https://github.com/tokio-rs/mini-redis/blob/tutorial/src/connection.rs#L159-L184).

Сначала обновляем структуру `Connection`:

```rust
use tokio::io::BufWriter;
use tokio::net::TcpStream;
use bytes::BytesMut;

pub struct Connection {
    stream: BufWriter<TcpStream>,
    buffer: BytesMut,
}

impl Connection {
    pub fn new(stream: TcpStream) -> Connection {
        Connection {
            stream: BufWriter::new(stream),
            buffer: BytesMut::with_capacity(4096),
        }
    }
}
```

Затем реализуем `write_frame()`:

```rust
use tokio::io::{self, AsyncWriteExt};
use mini_redis::Frame;

async fn write_frame(&mut self, frame: &Frame)
    -> io::Result<()>
{
    match frame {
        Frame::Simple(val) => {
            self.stream.write_u8(b'+').await?;
            self.stream.write_all(val.as_bytes()).await?;
            self.stream.write_all(b"\r\n").await?;
        }
        Frame::Error(val) => {
            self.stream.write_u8(b'-').await?;
            self.stream.write_all(val.as_bytes()).await?;
            self.stream.write_all(b"\r\n").await?;
        }
        Frame::Integer(val) => {
            self.stream.write_u8(b':').await?;
            self.write_decimal(*val).await?;
        }
        Frame::Null => {
            self.stream.write_all(b"$-1\r\n").await?;
        }
        Frame::Bulk(val) => {
            let len = val.len();

            self.stream.write_u8(b'$').await?;
            self.write_decimal(len as u64).await?;
            self.stream.write_all(val).await?;
            self.stream.write_all(b"\r\n").await?;
        }
        Frame::Array(_val) => unimplemented!(),
    }

    self.stream.flush().await;

    Ok(())
}
```

Используемые здесь функции предоставляются [AsyncWriteExt](https://docs.rs/tokio/1/tokio/io/trait.AsyncWriteExt.html). Они также доступны в `TcpStream`, но однобайтовую запись без промежуточного буфера выполнять не рекомендуется.

- [write_u8](https://docs.rs/tokio/1/tokio/io/trait.AsyncWriteExt.html#method.write_u8) записывает в файл один байт
- [write_all](https://docs.rs/tokio/1/tokio/io/trait.AsyncWriteExt.html#method.write_all) записывает весь фрагмент
- [write_decimal](https://github.com/tokio-rs/mini-redis/blob/tutorial/src/connection.rs#L225-L238) реализуется mini-redis

Функция заканчивается вызовом `self.stream.flush().await`. Поскольку `BufWriter` сохраняет записи в промежуточном буфере, вызовы `write()` не гарантируют, что данные будут записаны в сокет. Перед возвратом мы хотим, чтобы кадр был записан в сокет. Вызов `flush()` записывает в сокет любые данные, ожидающие обработки в буфере.

Другой альтернативой было бы не вызывать `flush()` в `write_frame()`. Вместо этого можно реализовать `flush()` у `Connection`. Это позволит вызывающей стороне записать в очередь несколько небольших кадров в буфер записи, а затем записать их все в сокет с помощью одного системного вызова `write()`. Это усложняет API `Connection`. Простота - одна из целей Mini-Redis, поэтому мы включили вызов `flush().await` в `write_frame()`.
