---
title: "Ловушки async/await"
description: "БлокировкаExecutor, Future traits, Pin"
date: 2026-05-20T05:00:00Z
weight: 28
image: "/images/rust/28-lovushki-async-await-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


`async/await` предоставляет удобную и эффективную абстракцию для параллельного асинхронного программирования. Однако модель `async/await` в `Rust` также имеет свои подводные камни и ловушки, о которых мы поговорим в этом разделе.

__Блокировка исполнителя__

Большинство асинхронных сред выполнения допускают одновременное выполнение только задач ввода-вывода. Это означает, что задачи блокировки ЦП будут блокировать исполнителя (executor) и препятствовать выполнению других задач. Простой обходной путь - использовать эквивалентные асинхронные методы там, где это возможно.

```rust
use futures::future::join_all;
use std::time::Instant;

async fn sleep_ms(start: &Instant, id: u64, duration_ms: u64) {
    std::thread::sleep(std::time::Duration::from_millis(duration_ms));
    println!(
        "фьючерс {id} спал в течение {duration_ms} мс, завершился после {} мс",
        start.elapsed().as_millis()
    );
}

#[tokio::main(flavor = "current_thread")]
async fn main() {
    let start = Instant::now();
    let sleep_futures = (1..=10).map(|t| sleep_ms(&start, t, t * 10));
    join_all(sleep_futures).await;
}
```

Ремарки:

- запустите код и убедитесь, что переходы в режим сна происходят последовательно, а не одновременно
- `flavor = "current_thread"` помещает все задачи в один поток. Это делает эффект более очевидным, но рассмотренная ошибка присутствует и в многопоточной версии
- замените `std::thread::sleep` на `tokio::time::sleep` и дождитесь результата
- другим решением может быть `tokio::task::spawn_blocking`, который порождает реальный поток и преобразует его дескриптор в `future`, не блокируя исполнителя
- о задачах не следует думать как о потоках ОС. Они не совпадают 1 к 1, и большинство исполнителей позволяют выполнять множество задач в одном потоке ОС. Это особенно проблематично при взаимодействии с другими библиотеками через `FFI`, где эта библиотека может зависеть от локального хранилища потоков или сопоставляться с конкретными потоками ОС (например, `CUDA`). В таких ситуациях отдавайте предпочтение `tokio::task::spawn_blocking`
- используйте синхронные мьютексы осторожно. Удержание мьютекса над `.await` может привести к блокировке другой задачи, которая может выполняться в том же потоке

__Pin__

Асинхронные блоки и функции возвращают типы, реализующие трейт `Future`. Возвращаемый тип является результатом преобразования компилятора, который превращает локальные переменные в данные, хранящиеся внутри фьючерса.

Некоторые из этих переменных могут содержать указатели на другие локальные переменные. По этой причине фьючерсы никогда не должны перемещаться в другую ячейку памяти, поскольку это сделает такие указатели недействительными.

Чтобы предотвратить перемещение фьючерса в памяти, его можно опрашивать только через закрепленный (pinned) указатель. `Pin` - это оболочка ссылки, которая запрещает все операции, которые могли бы переместить экземпляр, на который она указывает, в другую ячейку памяти.

```rust
use tokio::sync::{mpsc, oneshot};
use tokio::task::spawn;
use tokio::time::{sleep, Duration};

// Рабочая единица. В данном случае она просто спит в течение определенного времени
// и отвечает сообщением в канал `respond_on`
#[derive(Debug)]
struct Work {
    input: u32,
    respond_on: oneshot::Sender<u32>,
}

// Воркер, который ищет работу в очереди (queue) и выполняет ее
async fn worker(mut work_queue: mpsc::Receiver<Work>) {
    let mut iterations = 0;
    loop {
        tokio::select! {
            Some(work) = work_queue.recv() => {
                sleep(Duration::from_millis(10)).await; // выполняем "работу"
                work.respond_on
                    .send(work.input * 1000)
                    .expect("провал отправки ответа");
                iterations += 1;
            }
            // TODO: сообщать о количестве итераций каждый 100 мс
        }
    }
}

// "Запрашиватель" (requester), который запрашивает работу и ждет ее выполнения
async fn do_work(work_queue: &mpsc::Sender<Work>, input: u32) -> u32 {
    let (tx, rx) = oneshot::channel();
    work_queue
        .send(Work { input, respond_on: tx })
        .await
        .expect("провал отправки работы в очередь");
    rx.await.expect("провал ожидания ответа")
}

#[tokio::main]
async fn main() {
    let (tx, rx) = mpsc::channel(10);
    spawn(worker(rx));
    for i in 0..100 {
        let resp = do_work(&tx, i).await;
        println!("результат работы для итерации {i}: {resp}");
    }
}
```

Ремарки:

- в примере вы могли распознать шаблон актора (actor pattern). Акторы, как правило, вызывают `select!` в цикле
- это обобщение нескольких предыдущих уроков, так что не торопитесь
  - добавьте `_ = sleep(Duration::from_millis(100)) => { println!(..) }` в `select!`. Это никогда не выполнится. Почему?
  - теперь добавьте `timeout_fut`, содержащий этот фьючерс за пределами `loop`:

```rust
let mut timeout_fut = sleep(Duration::from_millis(100));
loop {
    select! {
        ..,
        _ = timeout_fut => { println!(..); },
    }
}
```

  - это также не будет работать. Изучите ошибки компилятора, добавьте `&mut` в `timeout_fut` в `select!` для решения проблемы перемещения, затем используйте `Box::pin`:

```rust
let mut timeout_fut = Box::pin(sleep(Duration::from_millis(100)));
loop {
    select! {
        ..,
        _ = &mut timeout_fut => { println!(..); },
    }
}
```

  - это компилируется, но по истечении тайм-аута на каждой итерации происходит `Poll::Ready` (для решения этой проблемы может помочь объединенный фьючерс). Обновите код, чтобы сбрасывать `timeout_fut` каждый раз, когда он истекает
- `Box` выделяет память в куче. В некоторых случаях `std::pin::pin!` - это тоже вариант, но его сложно использовать для фьючерса, которой переназначается
- другая альтернатива - вообще не использовать `pin`, а создать другую задачу, которая будет отправляться в канал `oneshot` каждые 100 мс
- данные, содержащие указатели на себя, называются самоссылающимися (self-referential). Обычно средство проверки заимствований (borrow checker) в `Rust` предотвращает перемещение таких данных, поскольку ссылки не могут жить дольше данных, на которые они указывают. Однако преобразование кода для асинхронных блоков и функций не проверяется средством проверки заимствований
- `Pin` - это обертка над ссылкой. Объект не может перемещаться с помощью закрепленного указателя. Однако он может перемещаться с помощью незакрепленного указателя
- метод `poll` трейта `Future` использует `Pin<&mut Self>` вместо `&mut Self` для ссылки на экземпляр. Вот почему он может вызываться только на закрепленном указателе

__Асинхронные трейты__

Асинхронные методы в трейтах пока не поддерживаются в стабильной версии `Rust`.

Крейт [async_trait](https://docs.rs/async-trait/latest/async_trait/) предоставляет макрос для решения этой задачи:

```rust
use async_trait::async_trait;
use std::time::Instant;
use tokio::time::{sleep, Duration};

#[async_trait]
trait Sleeper {
    async fn sleep(&self);
}

struct FixedSleeper {
    sleep_ms: u64,
}

#[async_trait]
impl Sleeper for FixedSleeper {
    async fn sleep(&self) {
        sleep(Duration::from_millis(self.sleep_ms)).await;
    }
}

async fn run_all_sleepers_multiple_times(
    sleepers: Vec<Box<dyn Sleeper>>,
    n_times: usize,
) {
    for _ in 0..n_times {
        println!("running all sleepers..");
        for sleeper in &sleepers {
            let start = Instant::now();
            sleeper.sleep().await;
            println!("slept for {}ms", start.elapsed().as_millis());
        }
    }
}

#[tokio::main]
async fn main() {
    let sleepers: Vec<Box<dyn Sleeper>> = vec![
        Box::new(FixedSleeper { sleep_ms: 50 }),
        Box::new(FixedSleeper { sleep_ms: 100 }),
    ];
    run_all_sleepers_multiple_times(sleepers, 5).await;
}
```

Ремарки:

- `async_trait` прост в использовании, но учтите, что для работы он использует выделение памяти в куче. Это влечет издержки производительности
- попробуйте создать новую "спящую" структуру, которая будет спать случайное время, и добавить ее в вектор

__Отмена__

Удаление фьючерса означает, что его больше никогда нельзя будет опросить. Это называется отменой (cancellation) и может произойти в любой момент ожидания. Необходимо позаботиться о том, чтобы система работала правильно даже в случае отмены фьючерса. Например, он не должен блокироваться или терять данные.

```rust
use std::io::{self, ErrorKind};
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt, DuplexStream};

struct LinesReader {
    stream: DuplexStream,
}

impl LinesReader {
    fn new(stream: DuplexStream) -> Self {
        Self { stream }
    }

    async fn next(&mut self) -> io::Result<Option<String>> {
        let mut bytes = Vec::new();
        let mut buf = [0];
        while self.stream.read(&mut buf[..]).await? != 0 {
            bytes.push(buf[0]);
            if buf[0] == b'\n' {
                break;
            }
        }
        if bytes.is_empty() {
            return Ok(None);
        }
        let s = String::from_utf8(bytes)
            .map_err(|_| io::Error::new(ErrorKind::InvalidData, "не UTF-8"))?;
        Ok(Some(s))
    }
}

async fn slow_copy(source: String, mut dest: DuplexStream) -> std::io::Result<()> {
    for b in source.bytes() {
        dest.write_u8(b).await?;
        tokio::time::sleep(Duration::from_millis(10)).await
    }
    Ok(())
}

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let (client, server) = tokio::io::duplex(5);
    let handle = tokio::spawn(slow_copy("привет\nпривет\n".to_owned(), client));

    let mut lines = LinesReader::new(server);
    let mut interval = tokio::time::interval(Duration::from_millis(60));
    loop {
        tokio::select! {
            _ = interval.tick() => println!("тик!"),
            line = lines.next() => if let Some(l) = line? {
                print!("{}", l)
            } else {
                break
            },
        }
    }
    handle.await.unwrap()?;
    Ok(())
}
```

Ремарки:

- компилятор не помогает с обеспечением безопасности отмены. Необходимо читать документацию API и понимать, каким состоянием владеет ваша `async fn`
- в отличие от `panic!` и `?`, отмена - это часть нормального управления потоком выполнения (а не обработка ошибок)
- в примере теряется часть строки
  - если ветвь `tick()` выполняется первой, `next()` и его `buf` уничтожаются
  - `LinesReader ` можно сделать безопасным для отмены путем включения `buf` в структуру:

```rust
struct LinesReader {
    stream: DuplexStream,
    bytes: Vec<u8>,
    buf: [u8; 1],
}

impl LinesReader {
    fn new(stream: DuplexStream) -> Self {
        Self { stream, bytes: Vec::new(), buf: [0] }
    }
    async fn next(&mut self) -> io::Result<Option<String>> {
        // ...
        let raw = std::mem::take(&mut self.bytes);
        let s = String::from_utf8(raw)
        // ...
    }
}
```

- [Interval::tick](https://docs.rs/tokio/latest/tokio/time/struct.Interval.html#method.tick) безопасен для отмены, поскольку он отслеживает, был ли "доставлен" (delivered) тик
- [AsyncReadExt::read](https://docs.rs/tokio/latest/tokio/io/trait.AsyncReadExt.html#method.read) безопасен для отмены, поскольку он либо возвращается, либо не читает данные
- [AsyncBufReadExt::read_line](https://docs.rs/tokio/latest/tokio/io/trait.AsyncBufReadExt.html#method.read_line), как и пример, не является безопасным для отмены. Подробности и альтернативы см. в документации
