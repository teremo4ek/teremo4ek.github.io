---
title: "Трейты стандартной библиотеки"
description: "FromIterator, Read/Write, Default, операторы сравнения, замыкания"
date: 2026-05-20T05:00:00Z
weight: 11
image: "/images/rust/11-trejty-standartnoj-biblioteki-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


Рекомендуется внимательно ознакомиться с документацией каждого трейта.

__Сравнения__

Эти трейты поддерживают сравнение между значениями. Они могут реализовываться на типах, содержащих поля, которые реализуют эти трейты.

_PartialEq и Eq_

`PartialEq` - это отношение частичной эквивалентности (partial equivalence relation), с требуемым методом `eq()` и предоставляемым методом `ne()`. Эти методы вызываются операторами `==` и `!=`.

```rust
struct Key {
    id: u32,
    metadata: Option<String>,
}

impl PartialEq for Key {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}
```

`Eq` - это отношение полной эквивалентности (рефлексивное, симметричное и транзитивное), реализующее `PartialEq`. Функции, требующие полную эквивалентность, используют `Eq` как ограничивающий трейт (trait bound).

`PartialEq` может быть реализован для разных типов, а `Eq` нет, поскольку он является рефлексивным:

```rust
struct Key {
    id: u32,
    metadata: Option<String>,
}

impl PartialEq<u32> for Key {
    fn eq(&self, other: &u32) -> bool {
        self.id == *other
    }
}
```

_PartialOrd и Ord_

`PartialOrd` определяет частичный порядок (partial ordering), с методом `partial_cmp()`. Этот метод используется для реализации операторов `<`, `<=`, `>=` и `>`.

```rust
use std::cmp::Ordering;

#[derive(Eq, PartialEq)]
struct Citation {
    author: String,
    year: u32,
}

impl PartialOrd for Citation {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        match self.author.partial_cmp(&other.author) {
            Some(Ordering::Equal) => self.year.partial_cmp(&other.year),
            author_ord => author_ord,
        }
    }
}
```

`Ord` - это тотальный (total) порядок, с методом `cmp()`, возвращающим `Ordering`.

На практике эти трейты чаще реализуются автоматически (`derive`), чем вручную.

__Операторы__

Перегрузка операторов реализуется с помощью трейта [std::ops](https://doc.rust-lang.org/std/ops/index.html):

```rust
#[derive(Debug, Copy, Clone)]
struct Point {
    x: i32,
    y: i32,
}

impl std::ops::Add for Point {
    type Output = Self;

    fn add(self, other: Self) -> Self {
        Self { x: self.x + other.x, y: self.y + other.y }
    }
}

fn main() {
    let p1 = Point { x: 10, y: 20 };
    let p2 = Point { x: 100, y: 200 };
    println!("{:?} + {:?} = {:?}", p1, p2, p1 + p2);
}
```

- Мы можем реализовать `Add` для `&Point`. В каких случаях это может быть полезным?
  - Ответ: `Add::add()` потребляет `self`. Если тип `T`, для которого перегружается оператор, не является `Copy` (копируемым), мы должны реализовать перегрузку оператора для `&T`. Это позволяет избежать необходимости явного клонирования при вызове
- Почему `Output` является ассоциированным типом? Можем ли мы сделать его параметром типа или метода?
  - Короткий ответ: параметры типа функции контролируются вызывающим, а ассоциированные типы (`Output`) - тем, кто реализует трейт
- Мы можем реализовать `Add` для двух разных типов, например, `impl Add<(i32, i32)> for Point` добавит кортеж в `Point`

__From и Into__

Типы, реализующие трейты [From](https://doc.rust-lang.org/std/convert/trait.From.html) и [Into](https://doc.rust-lang.org/std/convert/trait.Into.html), могут преобразовываться в другие типы:

```rust
fn main() {
    let s = String::from("hello");
    let addr = std::net::Ipv4Addr::from([127, 0, 0, 1]);
    let one = i16::from(true);
    let bigger = i32::from(123_i16);
    println!("{s}, {addr}, {one}, {bigger}");
}
```

`Into` автоматически реализуется при реализации `From`:

```rust
fn main() {
    let s: String = "hello".into();
    let addr: std::net::Ipv4Addr = [127, 0, 0, 1].into();
    let one: i16 = true.into();
    let bigger: i32 = 123_i16.into();
    println!("{s}, {addr}, {one}, {bigger}");
}
```

__Приведение типов__

`Rust` поддерживает как неявное приведение (преобразование) типов (casting), так и явное с помощью `as`:

```rust
fn main() {
    let value: i64 = 1000;
    println!("as u16: {}", value as u16);
    println!("as i16: {}", value as i16);
    println!("as u8: {}", value as u8);
}
```

Результаты `as` всегда определяются в `Rust`, поэтому являются согласованными на разных платформах. Это может не соответствовать нашему интуитивному мнению об изменении знака или приведении к меньшему типу.

Приведение типов с помощью `as` - это относительно сложный инструмент, который легко использовать неправильно и который может стать источником мелких ошибок, поскольку используемые типы или диапазоны значений в них могут легко измениться. Приведение лучше всего использовать тогда, когда целью является указать безусловное усечение (unconditional truncation) (например, выбор нижних 32 битов `u64` с помощью `as u32`, независимо от того, что было в старших битах).

Для приведения, которое всегда можно выполнить успешно (например, из `u32` в `u64`), предпочтительнее использовать `From` или `Into`. Для приведения, которое в некоторых случаях выполнить невозможно, доступны `TryFrom` и `TryInto`, которые позволяют по-разному обрабатывать случаи возможности и невозможности приведения одного типа к другому.

__Read и Write__

[Read](https://doc.rust-lang.org/std/io/trait.Read.html) и [BufRead](https://doc.rust-lang.org/std/io/trait.BufRead.html) позволяют абстрагироваться от источников (sources) `u8`:

```rust
use std::io::{BufRead, BufReader, Read, Result};

fn count_lines<R: Read>(reader: R) -> usize {
    let buf_reader = BufReader::new(reader);
    buf_reader.lines().count()
}

// Здесь `Result<T>` из `std::io` == `Result<T, std::io::Error>`
fn main() -> Result<()> {
    let slice: &[u8] = b"foo\nbar\nbaz\n";
    println!("строк в срезе: {}", count_lines(slice));

    let file = std::fs::File::open(std::env::current_exe()?)?;
    println!("строк в файле: {}", count_lines(file));
    Ok(())
}
```

[Write](https://doc.rust-lang.org/std/io/trait.Write.html), в свою очередь, позволяет абстрагироваться от приемников (sinks) `u8`:

```rust
use std::io::{Result, Write};

fn log<W: Write>(writer: &mut W, msg: &str) -> Result<()> {
    writer.write_all(msg.as_bytes())?;
    writer.write_all("\n".as_bytes())
}

fn main() -> Result<()> {
    let mut buffer = Vec::new();
    log(&mut buffer, "Hello")?;
    log(&mut buffer, "World")?;
    println!("{:?}", buffer);
    Ok(())
}
```

__Трейт Default__

Трейт [Default](https://doc.rust-lang.org/std/default/trait.Default.html) генерирует дефолтное значение типа:

```rust
#[derive(Debug, Default)]
struct Derived {
    x: u32,
    y: String,
    z: Implemented,
}

#[derive(Debug)]
struct Implemented(String);

impl Default for Implemented {
    fn default() -> Self {
        Self("Иван Петров".into())
    }
}

fn main() {
    let default_struct = Derived::default();
    println!("{default_struct:#?}");

    let almost_default_struct =
        Derived { y: "Y установлена!".into(), ..Derived::default() };
    println!("{almost_default_struct:#?}");

    let nothing: Option<Derived> = None;
    println!("{:#?}", nothing.unwrap_or_default());
}
```

Ремарки:

- `Default` может быть реализован как вручную, так и с помощью `derive`
- автоматическая реализация создает значение, в котором для всех полей установлены значения по умолчанию
  - это означает, что все поля структуры также должны реализовывать `Default`
- стандартные типы `Rust` часто реализуют `Default` с разумными значениями (`0`, `""` и т.д.)
- частичная инициализация структуры хорошо работает с `Default`
- стандартная библиотека `Rust` знает, что типы могут реализовывать `Default`, и предоставляет удобные методы, которые его используют
- синтаксис `..` называется [синтаксисом обновления структуры](https://doc.rust-lang.org/book/ch05-01-defining-structs.html#creating-instances-from-other-instances-with-struct-update-syntax)

__Замыкания__

Замыкания (closures) или лямбда-выражения имеют типы, которым нельзя дать имя. Однако они реализуют специальные трейты [Fn](https://doc.rust-lang.org/std/ops/trait.Fn.html), [FnMut](https://doc.rust-lang.org/std/ops/trait.FnMut.html) и [FnOnce](https://doc.rust-lang.org/std/ops/trait.FnOnce.html):

```rust
fn apply_with_log(func: impl FnOnce(i32) -> i32, input: i32) -> i32 {
    println!("вызов функции на {input}");
    func(input)
}

fn main() {
    let add_3 = |x| x + 3;
    println!("add_3: {}", apply_with_log(add_3, 10));
    println!("add_3: {}", apply_with_log(add_3, 20));

    let mut v = Vec::new();
    let mut accumulate = |x: i32| {
        v.push(x);
        v.iter().sum::<i32>()
    };
    println!("accumulate: {}", apply_with_log(&mut accumulate, 4));
    println!("accumulate: {}", apply_with_log(&mut accumulate, 5));

    let multiply_sum = |x| x * v.into_iter().sum::<i32>();
    println!("multiply_sum: {}", apply_with_log(multiply_sum, 3));
}
```

Ремарки:

- `Fn` (например, `add_3`) не потребляет и не изменяет захваченные значения или, возможно, вообще ничего не захватывает. Ее можно вызывать несколько раз одновременно
- `FnMut` (например, `accumulate`) может менять захваченные значения. Ее можно вызывать несколько раз, но не одновременно
- `FnOnce` (например, `multiply_sum`) можно вызвать только один раз. Она может потреблять захваченные значения
- `FnMut` - это подтип (подтрейт - subtrait) `FnOnce`. `Fn` - это подтип `FnMut` и `FnOnce`. Это означает, что мы можем использовать `FnMut` там, где ожидается `FnOnce`, и `Fn` там, где ожидается `FnMut` или `FnOnce`
- при определении функции, принимающей замыкание, мы должны сначала брать `FnOnce`, затем `FnMut` и в конце `Fn` как наиболее гибкий тип
- напротив, при определении замыкания мы начинаем с `Fn`
- по умолчанию замыкание захватывают значение по ссылке. Ключевое слово `move` позволяет замыканию захватывать само значение

```rust
fn make_greeter(prefix: String) -> impl Fn(&str) {
    return move |name| println!("{} {}", prefix, name);
}

fn main() {
    let hi = make_greeter("привет".to_string());
    hi("всем");
}
```

__Упражнение: ROT13__

В этом упражнении мы реализуем классический шифр ["ROT13"](https://ru.wikipedia.org/wiki/ROT13).

Меняйте только алфавитные символы `ASCII`, чтобы результат оставался валидным `UTF-8`.

```rust
use std::io::Read;

struct RotDecoder<R: Read> {
    input: R,
    rot: u8,
}

impl<R: Read> Read for RotDecoder<R> {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        todo!("реализуй меня")
    }
}

fn main() {
    let mut rot =
        RotDecoder { input: "Gb trg gb gur bgure fvqr!".as_bytes(), rot: 13 };
    let mut result = String::new();
    // `read_to_string()` вызывает `read()` под капотом и преобразует его результат в строку
    rot.read_to_string(&mut result).unwrap();
    println!("{}", result);
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn joke() {
        let mut rot =
            RotDecoder { input: "Gb trg gb gur bgure fvqr!".as_bytes(), rot: 13 };
        let mut result = String::new();
        rot.read_to_string(&mut result).unwrap();
        assert_eq!(&result, "To get to the other side!");
    }

    #[test]
    fn binary() {
        let input: Vec<u8> = (0..=255u8).collect();
        let mut rot = RotDecoder::<&[u8]> { input: input.as_ref(), rot: 13 };
        let mut buf = [0u8; 256];
        assert_eq!(rot.read(&mut buf).unwrap(), 256);
        for i in 0..=255 {
            if input[i] != buf[i] {
                assert!(input[i].is_ascii_alphabetic());
                assert!(buf[i].is_ascii_alphabetic());
            }
        }
    }
}
```

<details>
<summary>Решение:</summary>

```rust
impl<R: Read> Read for RotDecoder<R> {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        // Читаем данные в буфер
        let size = self.input.read(buf)?;
        // Перебираем байты
        for b in &mut buf[..size] {
            // Только буквы алфавита
            if b.is_ascii_alphabetic() {
                // База
                let base = if b.is_ascii_uppercase() { 'A' } else { 'a' } as u8;
                // Сдвигаем на `rot` в пределах 26 (количество букв в английском алфавите)
                *b = (*b - base + self.rot) % 26 + base;
            }
        }
        // Возвращаем "сдвинутые" байты
        Ok(size)
    }
}
```

</details>
