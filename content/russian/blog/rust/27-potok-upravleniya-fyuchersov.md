---
title: "Поток управления фьючерсов"
description: "Асинхронные циклы, join!, select!,.cancel"
date: 2026-05-20T05:00:00Z
weight: 27
image: "/images/rust/27-potok-upravleniya-fyuchersov-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


Фьючерсы могут объединяться вместе для создания графов потоков параллельных вычислений. Мы уже видели задачи, которые функционируют как автономные потоки выполнения.

__Join__

Метод `join_all` ждет, когда все фьючерсы будут готовы, и возвращает их результаты. Это похоже на `Promise.all` в `JavaScript` или `asyncio.gather` в `Python`.

```rust
use anyhow::Result;
use futures::future;
use reqwest;
use std::collections::HashMap;

async fn size_of_page(url: &str) -> Result<usize> {
    let resp = reqwest::get(url).await?;
    Ok(resp.text().await?.len())
}

#[tokio::main]
async fn main() {
    let urls: [&str; 4] = [
        "https://google.com",
        "https://httpbin.org/ip",
        "https://play.rust-lang.org/",
        "BAD_URL",
    ];
    let futures_iter = urls.into_iter().map(size_of_page);
    let results = future::join_all(futures_iter).await;
    let page_sizes_dict: HashMap<&str, Result<usize>> =
        urls.into_iter().zip(results.into_iter()).collect();
    println!("{:?}", page_sizes_dict);
}
```

Ремарки:

- для нескольких фьючерсов непересекающихся типов можно использовать `std::future::join!` но мы должны знать, сколько фьючерсов у нас будет во время компиляции. В настоящее время `join_all()` находится в крейте `futures`, но скоро будет стабилизирован в `std::future`
- риск соединения заключается в том, что какой-нибудь фьючерс может никогда не разрешиться, что приведет к остановке программы
- мы можем комбинировать `join_all()` с `join!`, например, чтобы объединить все запросы к службе `HTTP`, а также запрос к базе данных. Попробуйте добавить `tokio::time::sleep()` во фьючерс, используя `future::join!`. Это не таймаут (для которого требуется `select!`, как описано в следующем разделе), а демонстрация работы `join!`

__Select__

Операция выбора (select) ждет готовности любого фьючерса из набора и реагирует на его результат. В `JavaScript` это похоже на `Promise.race`. В `Python` это похоже на `asyncio.wait(task_set, return_when=asyncio.FIRST_COMPLETED)`.

Подобно оператору `match`, тело `select!` имеет несколько ветвей (arms), каждая из которых имеет форму `pattern = future => statement`. Когда `future` готов, его возвращаемое значение деструктурируется `pattern`. Затем `statement` запускается с итоговыми переменными. Результат `statement` становится результатом макроса `select!`.

```rust
use tokio::sync::mpsc::{self, Receiver};
use tokio::time::{sleep, Duration};

#[derive(Debug, PartialEq)]
enum Animal {
    Cat { name: String },
    Dog { name: String },
}

async fn first_animal_to_finish_race(
    mut cat_rcv: Receiver<String>,
    mut dog_rcv: Receiver<String>,
) -> Option<Animal> {
    tokio::select! {
        cat_name = cat_rcv.recv() => Some(Animal::Cat { name: cat_name? }),
        dog_name = dog_rcv.recv() => Some(Animal::Dog { name: dog_name? })
    }
}

#[tokio::main]
async fn main() {
    let (cat_sender, cat_receiver) = mpsc::channel(32);
    let (dog_sender, dog_receiver) = mpsc::channel(32);

    tokio::spawn(async move {
        sleep(Duration::from_millis(500)).await;
        cat_sender.send(String::from("Феликс")).await.expect("ошибка отправки имени кота");
    });

    tokio::spawn(async move {
        sleep(Duration::from_millis(50)).await;
        dog_sender.send(String::from("Рекс")).await.expect("ошибка отправки имени собаки");
    });

    let winner = first_animal_to_finish_race(cat_receiver, dog_receiver)
        .await
        .expect("ошибка получения победителя");

    println!("Победителем является {winner:?}");
}
```

Ремарки:

- в примере у нас имеется гонка между кошкой и собакой. `first_animal_to_finish_race()` "слушает" (listening) оба канала и возвращает первый по времени результат. Поскольку имя собаки прибывает через 50 мс, собака выигрывает у кошки, имя которой прибывает через 500 мс
- в примере вместо `channel` можно использовать `oneshot`, поскольку предполагается однократный вызов метода `send`
- попробуйте добавить к гонке дедлайн, демонстрируя выбор разных фьючерсов
- обратите внимание, что `select!` уничтожает не совпавшие ветви, что отменяет их фьючерсы. `select!` легче всего использовать, когда каждое выполнение этого макроса создает новые фьючерсы
  - альтернативой является передача `&mut future` вместо самого фьючерса, но это может привести к проблемам, о котором мы поговорим позже
