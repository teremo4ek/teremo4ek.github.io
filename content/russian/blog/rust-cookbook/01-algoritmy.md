---
title: "Алгоритмы"
description: "Генерация произвольных значений и сортировка векторов в Rust"
date: 2026-05-14T05:00:00Z
weight: 1
image: "/images/rust-cookbook/01-algoritmy-cover.png"
categories: ["Rust"]
tags: ["rust", "алгоритмы"]
---

## Генерация произвольных значений

### Генерация произвольных чисел

Генерация произвольных чисел выполняется с помощью метода `rand::thread_rng` генератора `rand::Rng`. Генератор создается отдельно для каждого потока (thread). Целые числа равномерно распределяются (uniform distribution) по диапазону типа, числа с плавающей запятой/точкой равномерно распределяются от 0 до, но не включая 1.

```rust
use rand::Rng;

fn main() {
    let mut rng = rand::thread_rng();

    let n1: u8 = rng.gen();
    let n2: u16 = rng.gen();
    println!("Произвольное u8: {}", n1);
    println!("Произвольное u16: {}", n2);
    println!("Произвольное u32: {}", rng.gen::<u32>());
    println!("Произвольное i32: {}", rng.gen::<i32>());
    println!("Произвольное число с плавающей точкой: {}", rng.gen::<f64>());
}
```

### Генерация произвольных чисел в заданном диапазоне

Пример генерации произвольного числа в диапазоне [0, 10) (не включая 10) с помощью метода `Rng::gen_range`:

```rust
use rand::Rng;

fn main() {
    let mut rng = rand::thread_rng();
    println!("Целое число: {}", rng.gen_range(0..10));
    println!("Число с плавающей точкой: {}", rng.gen_range(0.0..10.0));
}
```

Структура `Uniform` позволяет генерировать равномерно распределенные значения. Результат такой же, но операция может выполняться быстрее при повторной генерации чисел в аналогичном диапазоне.

```rust
use rand::distributions::{Distribution, Uniform};

fn main() {
    let mut rng = rand::thread_rng();
    let die = Uniform::from(1..7);

    loop {
        let throw = die.sample(&mut rng);
        println!("Результат броска кубика: {}", throw);
        if throw == 6 {
            break;
        }
    }
}
```

### Генерация произвольных чисел с заданным распределением

По умолчанию произвольные числа в крейте `rand` имеют равномерное распределение (uniform distribution). Крейт `rand_distr` предоставляет другие виды распределения. Сначала создается экземпляр распределения, затем — образец распределения с помощью метода `Distribution::sample`, которому передается генератор `rand::Rng`.

Пример использования нормального распределения:

```rust
use rand_distr::{Distribution, Normal, NormalError};
use rand::thread_rng;

fn main() -> Result<(), NormalError> {
    let mut rng = thread_rng();
    let normal = Normal::new(2.0, 3.0)?;
    let v = normal.sample(&mut rng);
    println!("{} из N(2, 9) распределения", v);
    Ok(())
}
```

### Генерация произвольных значений кастомного типа

Пример произвольной генерации кортежа `(i32, bool, f64)` и переменной пользовательского типа `Point`. Для произвольной генерации на типе `Point` реализуется трейт `Distribution` для структуры `Standard`.

```rust
use rand::Rng;
use rand::distributions::{Distribution, Standard};

#[derive(Debug)]
struct Point {
    x: i32,
    y: i32,
}

impl Distribution<Point> for Standard {
    fn sample<R: Rng + ?Sized>(&self, rng: &mut R) -> Point {
        let (rand_x, rand_y) = rng.gen();

        Point {
            x: rand_x,
            y: rand_y,
        }
    }
}

fn main() {
    let mut rng = rand::thread_rng();
    let rand_tuple = rng.gen::<(i32, bool, f64)>();
    let rand_point: Point = rng.gen();
    println!("Произвольный кортеж: {:?}", rand_tuple);
    println!("Произвольная структура Point: {:?}", rand_point);
}
```

### Генерация произвольного пароля из набора букв и чисел

Пример генерации строки заданной длины, состоящей из символов ASCII в диапазоне A-Z, a-z, 0-9, с помощью образца `Alphanumeric`:

```rust
use rand::{thread_rng, Rng};
use rand::distributions::Alphanumeric;

fn main() {
    let rand_string: String = thread_rng()
        .sample_iter(&Alphanumeric)
        .take(30)
        .map(char::from)
        .collect();

    println!("{}", rand_string);
}
```

### Генерация произвольного пароля из набора пользовательских символов

Пример генерации строки заданной длины, состоящей из символов ASCII кастомной пользовательской байтовой строкой, с помощью метода `Rng::gen_range`:

```rust
fn main() {
    use rand::Rng;
    const CHARSET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ\
                            abcdefghijklmnopqrstuvwxyz\
                            0123456789)(*&^%$#@!~";
    const PASSWORD_LEN: usize = 30;
    let mut rng = rand::thread_rng();

    let password: String = (0..PASSWORD_LEN)
        .map(|_| {
            let idx = rng.gen_range(0..CHARSET.len());
            CHARSET[idx] as char
        })
        .collect();

    println!("{:?}", password);
}
```

## Сортировка векторов

### Сортировка вектора целых чисел

Пример сортировки вектора целых чисел с помощью метода `vec::sort`. Метод `vec::sort_unstable` может быть быстрее, но не гарантирует порядок одинаковых элементов.

```rust
fn main() {
    let mut vec = vec![1, 5, 10, 2, 15];

    vec.sort();

    assert_eq!(vec, vec![1, 2, 5, 10, 15]);
}
```

### Сортировка вектора чисел с плавающей точкой

Вектор чисел с плавающей точкой может быть отсортирован с помощью методов `vec::sort_by` и `PartialOrd::partial_cmp`:

```rust
fn main() {
    let mut vec = vec![1.1, 1.15, 5.5, 1.123, 2.0];

    vec.sort_by(|a, b| a.partial_cmp(b).unwrap());

    assert_eq!(vec, vec![1.1, 1.123, 1.15, 2.0, 5.5]);
}
```

### Сортировка вектора структур

Пример сортировки вектора структур `Person` со свойствами `name` и `age` в естественном порядке (по имени и возрасту). Для того, чтобы сделать `Person` сортируемой, требуется реализация четырех трейтов: `Eq`, `PartialEq`, `Ord` и `PartialOrd`. Эти трейты могут быть реализованы автоматически (derived). Для сортировки только по возрасту с помощью метода `vec::sort_by` необходимо реализовать кастомную функцию сравнения.

```rust
#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
struct Person {
    name: String,
    age: u32
}

impl Person {
    pub fn new(name: String, age: u32) -> Self {
        Person {
            name,
            age
        }
    }
}

fn main() {
    let mut people = vec![
        Person::new("Zoe".to_string(), 25),
        Person::new("Al".to_string(), 60),
        Person::new("John".to_string(), 1),
    ];

    // Сортируем людей в естественном порядке (по имени и возрасту)
    people.sort();

    assert_eq!(
        people,
        vec![
            Person::new("Al".to_string(), 60),
            Person::new("John".to_string(), 1),
            Person::new("Zoe".to_string(), 25),
        ]);

    // Сортируем людей по возрасту
    people.sort_by(|a, b| b.age.cmp(&a.age));

    assert_eq!(
        people,
        vec![
            Person::new("Al".to_string(), 60),
            Person::new("Zoe".to_string(), 25),
            Person::new("John".to_string(), 1),
        ]);
}
```
