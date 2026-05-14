---
title: "Параллелизм"
description: "Явные потоки, параллельная обработка данных и глобальное мутабельное состояние"
date: 2026-05-14T05:00:00Z
weight: 4
image: "/images/rust-cookbook/04-parallellizm-cover.png"
categories: ["Rust"]
tags: ["rust", "параллелизм"]
---

## Явные потоки

В следующем примере используется крейт `crossbeam`, который предоставляет структуры данных и функции для конкурентного (concurrent) и параллельного (parallel) программирования. Метод `Scope::spawn` создает (выделяет) новый поток с ограниченной областью видимости (scoped thread), который гарантированно завершается до возврата из замыкания, передаваемого в функцию `crossbeam::scope`, позволяя безопасно ссылаться на данные из вызывающей функции.

### Параллельная обработка массива

Делим массив пополам и обрабатываем половины в отдельных потоках:

```rust
fn main() {
    let arr = &[1, 25, -4, 10];
    let max = find_max(arr);
    assert_eq!(max, Some(25));
}

fn find_max(arr: &[i32]) -> Option<i32> {
    const THRESHOLD: usize = 2;

    if arr.len() <= THRESHOLD {
        return arr.iter().cloned().max();
    }

    let mid = arr.len() / 2;
    let (left, right) = arr.split_at(mid);

    crossbeam::scope(|s| {
        let thread_l = s.spawn(|_| find_max(left));
        let thread_r = s.spawn(|_| find_max(right));

        let max_l = thread_l.join().unwrap()?;
        let max_r = thread_r.join().unwrap()?;

        Some(max_l.max(max_r))
    })
    .unwrap()
}
```

### Создание параллельного конвейера

В следующем примере используются крейты `crossbeam` и `crossbeam_channel` для создания параллельного конвейера (pipeline). Есть источник данных (sender), приемник данных (receiver) и данные, которые обрабатываются двумя параллельными рабочими потоками (worker threads, workers) на пути от источника к приемнику.

Мы используем связанные (bounded) каналы с емкостью равной 1, создаваемые с помощью метода `crossbeam_channel::bounded`. Производитель должен находиться в собственном потоке, поскольку он производит сообщения чаще, чем "воркеры" могут их обработать.

```rust
use std::thread;
use std::time::Duration;
use crossbeam_channel::bounded;

fn main() {
    let (snd1, rcv1) = bounded(1);
    let (snd2, rcv2) = bounded(1);
    let n_msgs = 4;
    let n_workers = 2;

    crossbeam::scope(|s| {
        // Поток производителя
        s.spawn(|_| {
            for i in 0..n_msgs {
                snd1.send(i).unwrap();
                println!("Source sent {}", i);
            }
            drop(snd1);
        });

        // Параллельная обработка двумя потоками/воркерами
        for _ in 0..n_workers {
            let (sendr, recvr) = (snd2.clone(), rcv1.clone());
            s.spawn(move |_| {
                thread::sleep(Duration::from_millis(500));
                for msg in recvr.iter() {
                    println!("Worker {:?} received {}", thread::current().id(), msg);
                    sendr.send(msg * 2).unwrap();
                }
            });
        }
        drop(snd2);

        // Приемник
        for msg in rcv2.iter() {
            println!("Sink received {}", msg);
        }
    }).unwrap();
}
```

### Передача данных между потоками

Следующий пример демонстрирует использование крейта `crossbeam_channel` в схеме "один производитель — один потребитель" (single producer — single consumer, SPSC). Данные передаются из одного потока в другой через канал `crossbeam_channel::unbounded`.

```rust
use std::{thread, time};
use crossbeam_channel::unbounded;

fn main() {
    let (snd, rcv) = unbounded();
    let n_msgs = 5;

    crossbeam::scope(|s| {
        s.spawn(|_| {
            for i in 0..n_msgs {
                snd.send(i).unwrap();
                thread::sleep(time::Duration::from_millis(100));
            }
        });
    }).unwrap();

    for _ in 0..n_msgs {
        let msg = rcv.recv().unwrap();
        println!("{}", msg);
    }
}
```

### Глобальное мутабельное состояние

Пример создания глобального состояния с помощью крейта `lazy_static`. Макрос `lazy_static!` создает доступную глобально `static ref`, мутирование которой требует `Mutex`. Обертка `Mutex` гарантирует, что состояние может быть одновременно доступно только одному потоку, что позволяет избежать гонки за данными.

```rust
use error_chain::error_chain;
use lazy_static::lazy_static;
use std::sync::Mutex;

error_chain! {}

lazy_static! {
    static ref FRUIT: Mutex<Vec<String>> = Mutex::new(Vec::new());
}

fn insert(fruit: &str) -> Result<()> {
    let mut db = FRUIT.lock().map_err(|_| "Failed to acquire MutexGuard")?;
    db.push(fruit.to_string());
    Ok(())
}

fn main() -> Result<()> {
    insert("apple")?;
    insert("orange")?;
    insert("peach")?;
    {
        let db = FRUIT.lock().map_err(|_| "Failed to acquire MutexGuard")?;

        db.iter()
            .enumerate()
            .for_each(|(i, item)| println!("{}: {}", i, item));
    }
    insert("grape")?;
    Ok(())
}
```

## Параллельная обработка данных

### Параллельная модификация элементов массива

В следующем примере используется `rayon` — библиотека Rust для параллельной обработки данных. `rayon` предоставляет метод `par_iter_mut` для любого параллельно перебираемого типа данных.

```rust
use rayon::prelude::*;

fn main() {
    let mut arr = [0, 7, 9, 11];
    arr.par_iter_mut().for_each(|p| *p -= 1);
    println!("{:?}", arr);
}
```

### Параллельный поиск совпадения элемента с предикатом

Следующий пример демонстрирует использование методов `rayon::any` и `rayon::all`, которые являются "параллельными" аналогами `std::any` и `std::all`. `rayon::any` параллельно проверяет, совпадает ли какой-нибудь элемент итератора с предикатом и возвращается, как только такой элемент обнаружен. `rayon::all` параллельно проверяет, совпадают ли все элементы итератора с предикатом и возвращается, как только обнаружен несовпадающий элемент.

```rust
use rayon::prelude::*;

fn main() {
    let mut vec = vec![2, 4, 6, 8];

    assert!(!vec.par_iter().any(|n| (*n % 2) != 0));
    assert!(vec.par_iter().all(|n| (*n % 2) == 0));
    assert!(!vec.par_iter().any(|n| *n > 8 ));
    assert!(vec.par_iter().all(|n| *n <= 8 ));

    vec.push(9);

    assert!(vec.par_iter().any(|n| (*n % 2) != 0));
    assert!(!vec.par_iter().all(|n| (*n % 2) == 0));
    assert!(vec.par_iter().any(|n| *n > 8 ));
    assert!(!vec.par_iter().all(|n| *n <= 8 ));
}
```

### Параллельный поиск элемента

В следующем примере мы используем методы `rayon::find_any` и `par_iter` для поиска элемента в векторе, который удовлетворяет предикату в замыкании. `rayon::find_any` возвращает первый элемент, совпавший с предикатом.

```rust
use rayon::prelude::*;

fn main() {
    let v = vec![6, 2, 1, 9, 3, 8, 11];

    let f1 = v.par_iter().find_any(|&&x| x == 9);
    let f2 = v.par_iter().find_any(|&&x| x % 2 == 0 && x > 6);
    let f3 = v.par_iter().find_any(|&&x| x > 8);

    assert_eq!(f1, Some(&9));
    assert_eq!(f2, Some(&8));
    assert!(f3 > Some(&8));
}
```

### Параллельная сортировка вектора

Создаем вектор пустых строк. Метод `par_iter_mut().for_each` параллельно заполняет вектор произвольными значениями. `par_sort_unstable`, обычно, быстрее, чем алгоритмы стабильной сортировки.

```rust
use rand::distributions::Alphanumeric;
use rand::{thread_rng, Rng};
use rayon::prelude::*;

fn main() {
    let mut vec = vec![String::new(); 100];
    vec.par_iter_mut().for_each(|p| {
        let mut rng = thread_rng();

        *p = (0..5)
            .map(|_| rng.sample(&Alphanumeric))
            .map(char::from)
            .collect()
    });
    vec.par_sort_unstable();
    println!("{:?}", vec);
}
```

### Параллельный map-reduce

В следующем примере мы используем методы `rayon::filter`, `rayon::map` и `rayon::reduce` для вычисления среднего возраста людей (объект `Person`) старше 30 (поле `age`).

```rust
use rayon::prelude::*;

struct Person {
    age: u32,
}

fn main() {
    let v: Vec<Person> = vec![
        Person { age: 23 },
        Person { age: 19 },
        Person { age: 42 },
        Person { age: 17 },
        Person { age: 17 },
        Person { age: 31 },
        Person { age: 30 },
    ];

    let num_over_30 = v.par_iter().filter(|&x| x.age > 30).count() as f32;
    let sum_over_30 = v.par_iter()
        .map(|x| x.age)
        .filter(|&x| x > 30)
        .reduce(|| 0, |x, y| x + y);

    let alt_sum_30: u32 = v.par_iter()
        .map(|x| x.age)
        .filter(|&x| x > 30)
        .sum();

    let avg_over_30 = sum_over_30 as f32 / num_over_30;
    let alt_avg_over_30 = alt_sum_30 as f32/ num_over_30;

    assert!((avg_over_30 - alt_avg_over_30).abs() < std::f32::EPSILON);
    println!("The average age of people older than 30 is {}", avg_over_30);
}
```

### Параллельная генерация миниатюр в формате JPG

Метод `glob::glob_with` ищет файлы `.jpg` в текущей директории. `rayon` меняет размеры изображений с помощью метода `DynamicImage::resize`. Он делает это параллельно с помощью метода `par_iter`.

```rust
use error_chain::error_chain;

use std::fs::create_dir_all;
use std::path::Path;

use error_chain::ChainedError;
use glob::{glob_with, MatchOptions};
use image::{imageops::FilterType, ImageError};
use rayon::prelude::*;

error_chain! {
    foreign_links {
        Image(ImageError);
        Io(std::io::Error);
        Glob(glob::PatternError);
    }
}

fn main() -> Result<()> {
    let options: MatchOptions = Default::default();
    let files: Vec<_> = glob_with("*.jpg", options)?
        .filter_map(|x| x.ok())
        .collect();

    if files.len() == 0 {
        error_chain::bail!("No .jpg files found in current directory");
    }

    let thumb_dir = "thumbnails";
    create_dir_all(thumb_dir)?;

    println!("Saving {} thumbnails into '{}'...", files.len(), thumb_dir);

    let image_failures: Vec<_> = files
        .par_iter()
        .map(|path| {
            make_thumbnail(path, thumb_dir, 300)
                .map_err(|e| e.chain_err(|| path.display().to_string()))
        })
        .filter_map(|x| x.err())
        .collect();

    image_failures
        .iter()
        .for_each(|x| println!("{}", x.display_chain()));

    println!(
        "{} thumbnails saved successfully",
        files.len() - image_failures.len()
    );
    Ok(())
}

fn make_thumbnail<PA, PB>(original: PA, thumb_dir: PB, longest_edge: u32) -> Result<()>
where
    PA: AsRef<Path>,
    PB: AsRef<Path>,
{
    let img = image::open(original.as_ref())?;
    let file_path = thumb_dir.as_ref().join(original);

    Ok(img
        .resize(longest_edge, longest_edge, FilterType::Nearest)
        .save(file_path)?)
}
```
