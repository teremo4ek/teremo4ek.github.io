---
title: "Подробно об асинхронности"
description: "Фьючерсы, исполнители, будильники и реализация мини-Tokio"
date: 2026-05-20T05:00:00Z
weight: 8
image: "/images/tokio/08-asinkhronnost-cover.png"
categories: ["Rust"]
tags: ["rust", "tokio"]
---

Углубимся в модель асинхронной среды выполнения Rust.

## Фьючерсы (futures)

В качестве краткого обзора возьмем очень простую асинхронную функцию. В ней нет ничего нового.

```rust
use tokio::net::TcpStream;

async fn my_async_fn() {
    println!("hello from async");
    let _socket = TcpStream::connect("127.0.0.1:3000").await.unwrap();
    println!("async TCP operation complete");
}
```

Мы вызываем функцию, и она возвращает некоторое значение. Затем мы вызываем `.await` на этом значении.

```rust
#[tokio::main]
async fn main() {
    // В терминал пока ничего не выводится
    let what_is_this = my_async_fn();
    // Текст печатается в терминале, соединение
    // устанавливается и закрывается
    what_is_this.await;
}
```

Значение, возвращаемое `my_async_fn()`, является фьючером. Фьючер - это значение, которое реализует типаж [std::future::Future](https://doc.rust-lang.org/std/future/trait.Future.html), предоставляемый стандартной библиотекой.

Определение `std::future::Future`:

```rust
use std::pin::Pin;
use std::task::{Context, Poll};

pub trait Future {
    type Output;

    fn poll(self: Pin<&mut Self>, cx: &mut Context) -> Poll<Self::Output>;
}
```

[Связанный тип (associated type)](https://doc.rust-lang.org/book/ch19-03-advanced-traits.html#specifying-placeholder-types-in-trait-definitions-with-associated-types) `Output` - это тип, который будет создан во фьючере после его завершения. Тип [Pin](https://doc.rust-lang.org/std/pin/index.html) - это то, с помощью чего Rust поддерживает заимствования в асинхронных функциях.

В отличие от того, как фьючеры реализуются в других языках, фьючер Rust не представляет вычисления, происходящие в фоновом режиме, а является самими вычислениями. Владелец фьючера отвечает за выполнение (advance) вычислений путем его опроса (poll).

__Реализация `Future`__

Реализуем очень простой фьючер. Он будет делать следующее:

1. Ждать какое-то временя.
2. Выводить некоторый текст в STDOUT.
3. Возвращать строку.

```rust
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::{Duration, Instant};

struct Delay {
    when: Instant,
}

impl Future for Delay {
    type Output = &'static str;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<&'static str>
    {
        if Instant::now() >= self.when {
            println!("hello world");
            Poll::Ready("done")
        } else {
            // Пока не обращайте внимания на эту строку
            cx.waker().wake_by_ref();
            Poll::Pending
        }
    }
}

#[tokio::main]
async fn main() {
    let when = Instant::now() + Duration::from_millis(10);
    let future = Delay { when };

    let out = future.await;
    assert_eq!(out, "done");
}
```

__Асинхронная функция как фьючер__

В функции `main` мы создаем экземпляр фьючера и вызываем на нем `.await`. В асинхронных функциях мы можем вызывать `.await` для любого значения, реализующего `Future`. В свою очередь, вызов асинхронной функции возвращает анонимный тип, реализующий `Future`. В случае `async fn main()` сгенерированный фьючер выглядит примерно так:

```rust
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::{Duration, Instant};

enum MainFuture {
    // Инициализирован, не опрашивался
    State0,
    // Ждет `Delay` - строка `future.await`
    State1(Delay),
    // Фьючер завершен
    Terminated,
}

impl Future for MainFuture {
    type Output = ();

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<()>
    {
        use MainFuture::*;

        loop {
            match *self {
                State0 => {
                    let when = Instant::now() + Duration::from_millis(10);
                    let future = Delay { when };
                    *self = State1(future);
                }
                State1(ref mut my_future) => {
                    match Pin::new(my_future).poll(cx) {
                        Poll::Ready(out) => {
                            assert_eq!(out, "done");
                            *self = Terminated;
                            return Poll::Ready(());
                        }
                        Poll::Pending => {
                            return Poll::Pending;
                        }
                    }
                }
                Terminated => {
                    panic!("future polled after completion")
                }
            }
        }
    }
}
```

Фьючеры Rust - это машины состояний (state machines). Здесь `MainFuture` представлено как перечисление возможных состояний фьючера. Фьючер начинается в состоянии `State0`. Когда вызывается `call()`, фьючер пытается обновить свое внутреннее состояние. Если фьючер может завершиться, возвращается `Poll::Ready`, содержащий результат асинхронных вычислений.

Если фьючер не может завершиться, обычно из-за нехватки ресурсов, возвращается `Poll::Pending`. Получение `Poll::Pending` указывает вызывающей стороне, что фьючер завершится позже, и вызывающая сторона должна снова вызвать `call()` через какое-то время.

Мы также видим, что фьючеры состоят из других фьючеров. Вызов `call()` внешнего фьючера приводит к вызову `call()` внутреннего фьючера.

## Исполнители (executors)

Асинхронные функции Rust возвращают фьючеры. Для обновления состояния фьючера должен вызываться `call()`. Фьючеры состоят из других фьючеров. Вопрос в том, что вызывает `call()` самого внешнего фьючера?

Напомним, что для запуска асинхронных функций их необходимо либо передать в `tokio::spawn()`, либо сделать их основной функцией, помеченной с помощью `#[tokio::main]`. В результате сгенерированный внешний фьючер передается исполнителю Tokio. Исполнитель отвечает за вызов `Future::poll()` на внешнем фьючере, доводя асинхронные вычисления до завершения.

__Мини Tokio__

Чтобы лучше понять, как все это сочетается друг с другом, реализуем собственную минимальную версию Tokio! Полный код можно найти [здесь](https://github.com/tokio-rs/website/blob/master/tutorial-code/mini-tokio/src/main.rs).

```rust
use std::collections::VecDeque;
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::{Duration, Instant};
use futures::task;

fn main() {
    let mut mini_tokio = MiniTokio::new();

    mini_tokio.spawn(async {
        let when = Instant::now() + Duration::from_millis(10);
        let future = Delay { when };

        let out = future.await;
        assert_eq!(out, "done");
    });

    mini_tokio.run();
}

struct MiniTokio {
    tasks: VecDeque<Task>,
}

type Task = Pin<Box<dyn Future<Output = ()> + Send>>;

impl MiniTokio {
    fn new() -> MiniTokio {
        MiniTokio {
            tasks: VecDeque::new(),
        }
    }

    /// Создает фьючер на экземпляре mini-tokio
    fn spawn<F>(&mut self, future: F)
    where
        F: Future<Output = ()> + Send + 'static,
    {
        self.tasks.push_back(Box::pin(future));
    }

    fn run(&mut self) {
        let waker = task::noop_waker();
        let mut cx = Context::from_waker(&waker);

        while let Some(mut task) = self.tasks.pop_front() {
            if task.as_mut().poll(&mut cx).is_pending() {
                self.tasks.push_back(task);
            }
        }
    }
}
```

Это запускает асинхронный блок. Экземпляр `Delay` создается с указанной задержкой и "ожидается". Однако наша реализация на данный момент имеет серьезный недостаток. Наш исполнитель никогда не спит. Исполнитель непрерывно просматривает все порожденные фьючеры и опрашивает их. Большую часть времени фьючер не будет готов выполнять новую работу и будет возвращать `Poll::Pending`. Этот процесс будет сжигать циклы ЦП и, как правило, будет не очень эффективным.

В идеале мы хотим, чтобы mini-tokio опрашивал фьючеры только тогда, когда они готовы к выполнению новой задачи. Это происходит, когда ресурс, на котором заблокирована задача, готов выполнить запрошенную операцию. Если задача хочет прочитать данные из сокета TCP, мы должны опрашивать задачу только тогда, когда сокет TCP получил данные. В нашем случае задача блокируется при достижении указанного момента времени (`Instant`). В идеале, mini-tokio должен опрашивать задачу только по прошествии этого времени.

Для этого опрошенный, но не готовый ресурс должен отправить уведомление исполнителю при переходе в состояние готовности.

## Будильники (wakers)

Будильники - недостающая часть. Это система, с помощью которой ресурс может уведомить ожидающую задачу о том, что он готов продолжить выполнение операции.

Еще раз взглянем на определение `Future::poll()`:

```rust
fn poll(self: Pin<&mut Self>, cx: &mut Context)
    -> Poll<Self::Output>;
```

Аргумент `Context` метода `poll` имеет метод `waker`. Этот метод возвращает [Waker](https://doc.rust-lang.org/std/task/struct.Waker.html), привязанный к текущей задаче. У `Waker` есть метод `wake`. Вызов этого метода сигнализирует исполнителю, что связанную задачу следует запланировать для выполнения. Ресурсы вызывают `wake()`, когда переходят в состояние готовности, чтобы уведомить исполнителя о том, что опрос задачи может продолжиться.

__Обновление `Delay`__

Мы можем обновить `Delay`, чтобы использовать будильники:

```rust
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::{Duration, Instant};
use std::thread;

struct Delay {
    when: Instant,
}

impl Future for Delay {
    type Output = &'static str;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<&'static str>
    {
        if Instant::now() >= self.when {
            println!("hello world");
            Poll::Ready("done")
        } else {
            // Получаем дескриптор будильника для текущей задачи
            let waker = cx.waker().clone();
            let when = self.when;

            // Создаем поток таймера
            thread::spawn(move || {
                let now = Instant::now();

                if now < when {
                    thread::sleep(when - now);
                }

                waker.wake();
            });

            Poll::Pending
        }
    }
}
```

Теперь по истечении указанного времени вызывающая задача получит уведомление, и исполнитель запланирует ее повторный опрос. Следующим шагом будет обновление mini-tokio для регистрации уведомлений о пробуждении.

С нашей реализацией `Delay` все еще есть несколько проблем. Мы исправим их позже.

> Когда фьючер возвращает `Poll::Pending`, он должен гарантировать, что в какой-то момент будет подан сигнал о пробуждении. Если этого не сделать, задача будет "висеть" бесконечно.

Вспомним код `Delay`:

```rust
impl Future for Delay {
    type Output = &'static str;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>)
        -> Poll<&'static str>
    {
        if Instant::now() >= self.when {
            println!("hello world");
            Poll::Ready("done")
        } else {
            // !
            cx.waker().wake_by_ref();
            Poll::Pending
        }
    }
}
```

Прежде чем вернуть `Poll::Pending`, мы вызываем `cx.waker().wake_by_ref()`. Это необходимо для выполнения контракта фьючера. Возвращая `Poll::Pending`, мы отвечаем за вызов будильника. Поскольку мы еще не реализовали поток таймера (timer thread), то подаем встроенный сигнал. Это приводит к тому, что фьючер будет немедленно повторно запланирован, повторно выполнен и, вероятно, снова не будет готов к завершению.

_Обратите внимание_, что мы можем подавать сигнал чаще, чем это необходимо. В данном конкретном случае мы подаем сигнал о пробуждении, хотя вообще не готовы продолжать операцию. В этом нет ничего плохого, кроме ненужной траты ресурсов процессора. Однако эта конкретная реализация приведет к образованию цикла занятости (busy loop).

__Обновление Mini Tokio__

Следующим шагом будет обновление Mini Tokio для получения уведомлений о пробуждении. Мы хотим, чтобы исполнитель запускал задачи только после их пробуждения, и для этого Mini Tokio предоставит собственный будильник. Когда будильник вызывается, связанная с ним задача ставится в очередь на выполнение. Mini Tokio передает этот сигнал во фьючер при его опросе.

Обновленный Mini Tokio будет использовать канал для хранения запланированных задач. Каналы позволяют ставить задачи в очередь для выполнения из любого потока. Будильники должны реализовывать `Send` и `Sync`.

> Типажи `Send` и `Sync` - это маркерные типажи (marker traits), связанные с параллелизмом Rust. Типы, которые можно отправить в другой поток, реализуют `Send`. Большинство типов являются `Send`, но некоторые (вроде [Rc](https://doc.rust-lang.org/std/rc/struct.Rc.html)) не являются. Типы, к которым можно одновременно получить доступ через неизменяемые ссылки, реализуют `Sync`. Тип может быть `Send`, но не `Sync`. Хорошим примером является [Cell](https://doc.rust-lang.org/std/cell/struct.Cell.html), который можно изменить с помощью неизменяемой ссылки, и поэтому одновременный доступ к нему небезопасен.

Обновляем структуру `MiniTokio`:

```rust
use std::sync::mpsc;
use std::sync::Arc;

struct MiniTokio {
    scheduled: mpsc::Receiver<Arc<Task>>,
    sender: mpsc::Sender<Arc<Task>>,
}

struct Task {
    // TODO
}
```

Будильники являются `Sync` и могут клонироваться. При вызове `wake()` задача должна планироваться для выполнения. Для реализации этого у нас есть канал. При вызове `wake()` задача передается в отправляющую половину канала. Наша структура `Task` будет реализовывать логику пробуждения. Для этого ему необходимо содержать как порожденный фьючер, так и отправителя из канала. Мы поместим фьючер в структуру `TaskFuture` рядом с перечислением `Poll`, чтобы отслеживать результат  последнего вызова `Future::poll()`, который необходим для обработки ложных пробуждений. Более подробная информация представлена в реализации метода `poll` в `TaskFuture`.

```rust
use std::sync::{Arc, Mutex};

/// Структура, содержащая фьючер и результат
/// последнего вызова его метода `poll`
struct TaskFuture {
    future: Pin<Box<dyn Future<Output = ()> + Send>>,
    poll: Poll<()>,
}

struct Task {
    // `Mutex` позволяет `Task` реализовать `Sync`.
    // `task_future` доступна одновременно только одному потоку.
    // `Mutex` является опциональным. Настоящий Tokio
    // не использует здесь мьютекс, но настоящий Tokio содержит
    // гораздо больше строк кода, чем может уместиться на одной странице туториала
    task_future: Mutex<TaskFuture>,
    executor: mpsc::Sender<Arc<Task>>,
}

impl Task {
    fn schedule(self: &Arc<Self>) {
        self.executor.send(self.clone());
    }
}
```

Для планирования задачи, `Arc` клонируется и отправляется по каналу. Теперь нам нужно подключить функцию `schedule` к `std::task::Waker`. Стандартная библиотека предоставляет для этого низкоуровневый API с использованием [ручного построения vtable](https://doc.rust-lang.org/std/task/struct.RawWakerVTable.html). Эта стратегия обеспечивает максимальную гибкость для разработчиков, но требует некоторого небезопасного шаблонного кода. Вместо прямого использования [RawWakerVTable](https://doc.rust-lang.org/std/task/struct.RawWakerVTable.html) мы будем использовать утилиту [ArcWake](https://docs.rs/futures/0.3/futures/task/trait.ArcWake.html), предоставляемую крейтом [futures](https://docs.rs/futures/). Это позволит нам реализовать простой типаж, чтобы представить структуру `Task` как будильник.

Добавляем следующую зависимость в файл `Cargo.toml`:

```toml
futures = "0.3"
```

Затем реализуем [futures::task::ArcWake](https://docs.rs/futures/0.3/futures/task/trait.ArcWake.html):

```rust
use futures::task::{self, ArcWake};
use std::sync::Arc;

impl ArcWake for Task {
    fn wake_by_ref(arc_self: &Arc<Self>) {
        arc_self.schedule();
    }
}
```

Когда поток таймера вызывает `waker.wake()`, задача передается в канал. Реализуем получение и выполнение задач в функции `MiniTokio::run`:

```rust
impl MiniTokio {
    fn run(&self) {
        while let Ok(task) = self.scheduled.recv() {
            task.poll();
        }
    }

    /// Инициализирует новый экземпляр mini-tokio
    fn new() -> MiniTokio {
        let (sender, scheduled) = mpsc::channel();

        MiniTokio { scheduled, sender }
    }

    /// Создает фьючер на экземпляре mini-tokio.
    ///
    /// Данный фьючер обернут в `Task` и помещен в очередь `scheduled`.
    /// Он будет выполнен при вызове `run()`
    fn spawn<F>(&self, future: F)
    where
        F: Future<Output = ()> + Send + 'static,
    {
        Task::spawn(future, &self.sender);
    }
}

impl TaskFuture {
    fn new(future: impl Future<Output = ()> + Send + 'static) -> TaskFuture {
        TaskFuture {
            future: Box::pin(future),
            poll: Poll::Pending,
        }
    }

    fn poll(&mut self, cx: &mut Context<'_>) {
        // Разрешены ложные пробуждения, даже после того, как фьючер
        // вернул `Ready`. Однако опрос фьючера, вернувшего
        // `Ready`, не разрешен. Поэтому мы должны проверять,
        // что фьючер находится в режиме ожидания перед его вызовом.
        // В противном случае, может возникнуть паника
        if self.poll.is_pending() {
            self.poll = self.future.as_mut().poll(cx);
        }
    }
}

impl Task {
    fn poll(self: Arc<Self>) {
        // Создаем будильник из экземпляра `Task`.
        // Здесь используется реализация `ArcWake`
        let waker = task::waker(self.clone());
        let mut cx = Context::from_waker(&waker);

        // Никакой другой поток не может заблокировать `task_future`
        let mut task_future = self.task_future.try_lock().unwrap();

        // Опрашиваем внутренний фьючер
        task_future.poll(&mut cx);
    }

    // Создаем новую задачу с данным фьючером.
    //
    // Инициализируем новый `Task`, содержащий данный фьючер и помещаем его
    // в `sender`. Получатель канала получит задачу и выполнит ее
    fn spawn<F>(future: F, sender: &mpsc::Sender<Arc<Task>>)
    where
        F: Future<Output = ()> + Send + 'static,
    {
        let task = Arc::new(Task {
            task_future: Mutex::new(TaskFuture::new(future)),
            executor: sender.clone(),
        });

        let _ = sender.send(task);
    }
}
```

Здесь происходит много всего. Во-первых, реализован `MiniTokio::run()`. Функция работает в цикле, получая из канала запланированные задачи.

Функции `new` и `spawn` используют канал, а не `VecDeque`. Когда создаются новые задачи, им предоставляется клон отправителя, который задача может использовать для планирования во время выполнения.

Функция `Task::poll` создает будильник с помощью утилиты `ArcWake` из крейта `futures`. Будильник используется для создания `task::Context`. Этот `task::Context` передается в `poll()`.

## Резюме

Мы рассмотрели полный пример того, как работает асинхронный Rust. `async/await` в Rust обеспечивается типажами. Это позволяет сторонним крейтам, таким как Tokio, предоставлять детали реализации.

- Асинхронные операции Rust ленивы и требуют, чтобы вызывающая сторона опрашивала их
- будильники передаются фьючерсам, чтобы связать фьючер с вызывающей его задачей
- когда ресурс не готов завершить операцию, возвращается `Poll::Pending` и записывается будильник задачи
- когда ресурс становится готовым, об этом уведомляется будильник задачи
- исполнитель получает уведомление и планирует выполнение задачи
- задача опрашивается еще раз, на этот раз ресурс готов, и задача выполняется

## Ремарки

Помните, при реализации `Delay`, мы отметили, что нужно исправить еще несколько вещей. Асинхронная модель Rust позволяет одному фьючеру мигрировать между задачами во время их выполнения. Рассмотрим следующий код:

```rust
use futures::future::poll_fn;
use std::future::Future;
use std::pin::Pin;

#[tokio::main]
async fn main() {
    let when = Instant::now() + Duration::from_millis(10);
    let mut delay = Some(Delay { when });

    poll_fn(move |cx| {
        let mut delay = delay.take().unwrap();
        let res = Pin::new(&mut delay).poll(cx);

        assert!(res.is_pending());

        tokio::spawn(async move {
            delay.await;
        });

        Poll::Ready(())
    }).await;
}
```

Функция `poll_fn` создает экземпляр `Future` с помощью замыкания. Приведенный код создает экземпляр `Delay`, опрашивает его один раз, затем отправляет его в новую задачу, где он ожидается. `Delay::poll()` вызывается несколько раз с разными экземплярами `Waker`. В этом случае, мы должны убедиться, что вызов `wake()` на `Waker` передан самому последнему вызову `poll()`.

При реализации фьючера очень важно предполагать, что каждый вызов `poll()` может предоставлять другой экземпляр `Waker`. Функция `poll` должна обновлять любой ранее записанный `Waker` новым.

Наша более ранняя реализация `Delay` порождала новый поток при каждом его опросе. Это нормально, но может быть очень неэффективно, если он опрашивается слишком часто (например, если мы применяем `select!` для этого и другого фьючера, оба будут опрашиваться всякий раз, когда в любом из них происходит событие). Один из подходов к решению этой задачи - запоминать факт создания потока и создавать новый поток только в том случае, если он еще не создан. Однако при таком подходе, мы должны убедиться, что `Waker` потока обновляется при последующих вызовах `call()`, поскольку, в противном случае, мы активируем не самый последний `Waker`.

Нашу предыдущую реализацию можно исправить так:

```rust
use std::future::Future;
use std::pin::Pin;
use std::sync::{Arc, Mutex};
use std::task::{Context, Poll, Waker};
use std::thread;
use std::time::{Duration, Instant};

struct Delay {
    when: Instant,
    // Имеет значение `Some`, если поток создан, и `None`, в противном случае
    waker: Option<Arc<Mutex<Waker>>>,
}

impl Future for Delay {
    type Output = ();

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        // Проверяем текущий экземпляр. Если время истекло, значит
        // этот фьючер завершился, возвращаем `Poll::Ready`
        if Instant::now() >= self.when {
            return Poll::Ready(());
        }

        // Время не истекло. Если фьючер вызывается впервые,
        // создаем поток таймера. Если поток уже создан,
        // проверяем, что сохраненный `Waker` совпадает с `Waker` текущей задачи
        if let Some(waker) = &self.waker {
            let mut waker = waker.lock().unwrap();

            // Проверяем, что сохраненный `Waker` совпадает с `Waker` текущей задачи.
            // Это необходимо, поскольку экземпляр фьючера `Delay` может быть перемещен
            // в другую задачу между вызовами `poll()`. Если это произойдет,
            // будильник, содержащийся в данном `Context` будет отличаться, и мы должны
            // обновить хранящийся будильник для учета этого изменения
            if !waker.will_wake(cx.waker()) {
                *waker = cx.waker().clone();
            }
        } else {
            let when = self.when;
            let waker = Arc::new(Mutex::new(cx.waker().clone()));
            self.waker = Some(waker.clone());

            // `poll()` вызывается впервые, создаем поток таймера
            thread::spawn(move || {
                let now = Instant::now();

                if now < when {
                    thread::sleep(when - now);
                }

                // Время истекло. Уведомляем вызывающего, вызывая будильник
                let waker = waker.lock().unwrap();
                waker.wake_by_ref();
            });
        }

        // К этому моменту будильник сохранен и таймер запущен.
        // Время не истекло, следовательно, фьючер не завершился,
        // поэтому мы должны вернуть `Poll::Pending`.
        //
        // Контракт типажа `Future` требует, чтобы при возврате `Pending`
        // фьючер гарантировал уведомление будильника о
        // необходимости повторного опроса. В нашем случае,
        // возвращая здесь `Pending`, мы обещаем, что вызовем
        // будильник, содержащийся в аргументе `Context`,
        // по истечении запрошенного времени. Мы обеспечиваем это путем
        // создания потока таймера выше.
        //
        // Если мы забудем вызвать будильник, задача повиснет навсегда
        Poll::Pending
    }
}
```

Это немного сложно, но идея состоит в том, что при каждом вызове `poll()` фьючер проверяет, что переданный будильник совпадает с ранее записанным. Если будильники совпадают, больше делать нечего. Если они не совпадают, тогда записанный будильник обновляется.

__Утилиты `Notify`__

Мы продемонстрировали, как фьючер `Delay` можно реализовать вручную с помощью будильника. Будильники являются основой того, как работает асинхронный Rust. Обычно нет необходимости опускаться до этого уровня. Например, в случае с `Delay` мы могли бы полностью реализовать его с помощью `async/await`, используя утилиту [tokio::sync::Notify](https://docs.rs/tokio/1/tokio/sync/struct.Notify.html). Эта утилита предоставляет базовый механизм уведомления о задачах. Она обрабатывает подробную информацию о будильниках, включая проверку соответствия записанного будильника текущей задаче.

Используя `Notify`, мы можем реализовать функцию `delay` следующим образом:

```rust
use tokio::sync::Notify;
use std::sync::Arc;
use std::time::{Duration, Instant};
use std::thread;

async fn delay(dur: Duration) {
    let when = Instant::now() + dur;
    let notify = Arc::new(Notify::new());
    let notify_clone = notify.clone();

    thread::spawn(move || {
        let now = Instant::now();

        if now < when {
            thread::sleep(when - now);
        }

        notify_clone.notify_one();
    });


    notify.notified().await;
}
```
