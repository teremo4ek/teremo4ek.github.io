---
title: "Потоки (streams)"
description: "Типаж Stream, адаптеры, перебор и реализация потоков"
date: 2026-05-20T05:00:00Z
weight: 10
image: "/images/tokio/10-potoki-cover.png"
categories: ["Rust"]
tags: ["rust", "tokio"]
---

Поток - это асинхронная серия значений. Это асинхронный эквивалент [std::iter::Iterator](https://doc.rust-lang.org/book/ch13-02-iterators.html), представленный типажом [Stream](https://docs.rs/futures-core/0.3/futures_core/stream/trait.Stream.html). Потоки можно перебирать в асинхронных функциях. Их также можно трансформировать с помощью адаптеров. Tokio предоставляет несколько распространенных адаптеров в типаже [StreamExt](https://docs.rs/tokio-stream/0.1/tokio_stream/trait.StreamExt.html).

Tokio предоставляет поддержку потоков в отдельном крейте `tokio-stream`:

```toml
tokio-stream = "0.1"
```

> В настоящее время утилиты для работы с потоками Tokio находятся в крейте `tokio-stream`. После стабилизации `Stream` в стандартной библиотеке Rust, эти утилиты будут перемещены в крейт `tokio`.

## Перебор

В настоящее время язык программирования Rust не поддерживает асинхронные циклы `for`. Вместо этого перебор потоков выполняется с помощью цикла `while let` в сочетании с методом `StreamExt::next`:

```rust
use tokio_stream::StreamExt;

#[tokio::main]
async fn main() {
    let mut stream = tokio_stream::iter(&[1, 2, 3]);

    while let Some(v) = stream.next().await {
        println!("GOT = {:?}", v);
    }
}
```

Как и итераторы, метод `next` возвращает `Option<T>`, где `T` - тип значения потока. Получение `None` указывает на то, что итерация потока завершена.

__Трансляция Mini-Redis__

Рассмотрим немного более сложный пример с использованием клиента Mini-Redis. Полный код можно найти [здесь](https://github.com/tokio-rs/website/blob/master/tutorial-code/streams/src/main.rs).

```rust
use tokio_stream::StreamExt;
use mini_redis::client;

async fn publish() -> mini_redis::Result<()> {
    let mut client = client::connect("127.0.0.1:6379").await?;

    // Публикуем некоторые данные
    client.publish("numbers", "1".into()).await?;
    client.publish("numbers", "two".into()).await?;
    client.publish("numbers", "3".into()).await?;
    client.publish("numbers", "four".into()).await?;
    client.publish("numbers", "five".into()).await?;
    client.publish("numbers", "6".into()).await?;
    Ok(())
}

async fn subscribe() -> mini_redis::Result<()> {
    let client = client::connect("127.0.0.1:6379").await?;
    let subscriber = client.subscribe(vec!["numbers".to_string()]).await?;
    let messages = subscriber.into_stream();

    tokio::pin!(messages);

    while let Some(msg) = messages.next().await {
        println!("got = {:?}", msg);
    }

    Ok(())
}

#[tokio::main]
async fn main() -> mini_redis::Result<()> {
    tokio::spawn(async {
        publish().await
    });

    subscribe().await?;

    println!("done");

    Ok(())
}
```

Сначала создается задача для публикации сообщений на сервере Mini-Redis в канале `numbers`. Затем мы подписываемся на этот канал в основной задаче и отображаем полученные сообщения.

После подписки на вернувшемся подписчике вызывается метод [into_stream](https://docs.rs/mini-redis/0.4/mini_redis/client/struct.Subscriber.html#method.into_stream). Это потребляет `Subscriber`, возвращая поток, который выдает сообщения по мере их поступления. _Обратите внимание_, что перед перебором сообщений поток закрепляется в стеке с помощью макроса [tokio::pin!](https://docs.rs/tokio/1/tokio/macro.pin.html). Вызов `next()` для потока требует его закрепления. Функция `into_stream` возвращает незакрепленный поток, мы должны явно закрепить его, чтобы выполнить итерацию.

> Значение Rust "закрепляется", когда его больше нельзя перемещать в памяти. Ключевой особенностью закрепленного значения является то, что указатели на него всегда остаются действительными. Эта особенность используется `async/await` для поддержки заимствования данных через точки `.await`.

Если мы забудем закрепить поток, то получим ошибку.

Запускаем сервер Mini-Redis:

```bash
mini-redis-server
```

Запускаем пример:

```bash
got = Ok(Message { channel: "numbers", content: b"1" })
got = Ok(Message { channel: "numbers", content: b"two" })
got = Ok(Message { channel: "numbers", content: b"3" })
got = Ok(Message { channel: "numbers", content: b"four" })
got = Ok(Message { channel: "numbers", content: b"five" })
got = Ok(Message { channel: "numbers", content: b"6" })
```

Некоторые ранние сообщения могут быть пропущены, поскольку между подпиской и публикацией идет гонка. Программа никогда не завершается. Подписка на канал Mini-Redis остается активной, пока активен сервер.

Посмотрим, как мы можем работать с потоками, чтобы расширить эту программу.

## Адаптеры

Функции, которые принимают `Stream` и возвращают другой `Stream`, часто называют "адаптерами потока", поскольку они представляют собой форму "шаблона адаптера" (adapter pattern). Популярными адаптерами потока являются [map](https://docs.rs/tokio-stream/0.1/tokio_stream/trait.StreamExt.html#method.map), [take](https://docs.rs/tokio-stream/0.1/tokio_stream/trait.StreamExt.html#method.take) и [filter](https://docs.rs/tokio-stream/0.1/tokio_stream/trait.StreamExt.html#method.filter).

Обновим Mini-Redis, чтобы он завершал работу. После получения трех сообщений прекращаем получать сообщения. Это делается с помощью `take()`. Этот адаптер ограничивает поток так, чтобы он выдавал не более `n` сообщений:

```rust
let messages = subscriber
    .into_stream()
    .take(3);
```

Запускаем программу:

```bash
got = Ok(Message { channel: "numbers", content: b"1" })
got = Ok(Message { channel: "numbers", content: b"two" })
got = Ok(Message { channel: "numbers", content: b"3" })
```

На этот раз программа завершается.

Теперь давайте ограничим поток однозначными числами. Проверяем длину сообщения. Для отброса любого сообщения, не соответствующего предикату, используется `filter()`:

```rust
let messages = subscriber
    .into_stream()
    .filter(|msg| match msg {
        Ok(msg) if msg.content.len() == 1 => true,
        _ => false,
    })
    .take(3);
```

Запускаем программу:

```bash
got = Ok(Message { channel: "numbers", content: b"1" })
got = Ok(Message { channel: "numbers", content: b"3" })
got = Ok(Message { channel: "numbers", content: b"6" })
```

_Обратите внимание_, что порядок применения адаптеров имеет значение. Вызов `filter()`, а затем `take()` отличается от вызова `take()`, а затем `filter()`.

Наконец, приведем в порядок вывод, удалив часть `Ok(Message { ... })`. Это делается с помощью `map()`. Поскольку `map()` вызывается после `filter()`, мы знаем, что сообщение `Ok`, поэтому можем использовать `unwrap()`:

```rust
let messages = subscriber
    .into_stream()
    .filter(|msg| match msg {
        Ok(msg) if msg.content.len() == 1 => true,
        _ => false,
    })
    .map(|msg| msg.unwrap().content)
    .take(3);
```

Запускаем программу:

```rust
got = b"1"
got = b"3"
got = b"6"
```

`filter()` и `map()` можно объединить в один вызов с помощью [filter_map()](https://docs.rs/tokio-stream/0.1/tokio_stream/trait.StreamExt.html#method.filter_map).

Существуют и [другие адаптеры](https://docs.rs/tokio-stream/0.1/tokio_stream/trait.StreamExt.html).

## Реализация `Stream`

Типаж `Stream` очень похож на типаж `Future`:

```rust
use std::pin::Pin;
use std::task::{Context, Poll};

pub trait Stream {
    type Item;

    fn poll_next(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>
    ) -> Poll<Option<Self::Item>>;

    fn size_hint(&self) -> (usize, Option<usize>) {
        (0, None)
    }
}
```

Функция `Stream::poll_next` во многом похожа на функцию `Future::poll`, за исключением того, что ее можно вызывать повторно для получения нескольких значений из потока. Как мы видели в одном из предыдущих разделов, когда поток не готов вернуть значение, он возвращает `Poll::Pending`. При этом регистрируется будильник задачи. Как только поток должен быть снова опрошен, будильник получает уведомление.

Метод `size_hint` используется так же, как и с [итераторами](https://doc.rust-lang.org/book/ch13-02-iterators.html).

Обычно при реализации потока вручную, это делается путем композиции фьючеров и других потоков. В качестве примера перепишем фьючер `Delay`. Мы преобразуем его в поток, который выдает `()` три раза с интервалом 10 мс:

```rust
use tokio_stream::Stream;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::Duration;

struct Interval {
    rem: usize,
    delay: Delay,
}

impl Interval {
    fn new() -> Self {
        Self {
            rem: 3,
            delay: Delay { when: Instant::now() }
        }
    }
}

impl Stream for Interval {
    type Item = ();

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<Option<()>>
    {
        if self.rem == 0 {
            // Задержек больше нет
            return Poll::Ready(None);
        }

        match Pin::new(&mut self.delay).poll(cx) {
            Poll::Ready(_) => {
                let when = self.delay.when + Duration::from_millis(10);
                self.delay = Delay { when };
                self.rem -= 1;
                Poll::Ready(Some(()))
            }
            Poll::Pending => Poll::Pending,
        }
    }
}
```

__`async-stream`__

Реализация потоков вручную с помощью типажа `Stream` может быть утомительной. К сожалению, язык программирования Rust пока не поддерживает синтаксис `async/await` для определения потоков.

В качестве временного решения можно использовать крейт [async-stream](https://docs.rs/async-stream). Он предоставляет макрос `stream!`, который преобразует входные данные в поток. С помощью этого крейта вышеуказанный интервал можно реализовать следующим образом:

```rust
use async_stream::stream;
use std::time::{Duration, Instant};

stream! {
    let mut when = Instant::now();

    for _ in 0..3 {
        let delay = Delay { when };
        delay.await;
        yield ();
        when += Duration::from_millis(10);
    }
}
```
