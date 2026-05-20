---
title: "Типы стандартной библиотеки"
description: "Vec, String, Option, Result, HashMap и другие типы"
date: 2026-05-20T05:00:00Z
weight: 10
image: "/images/rust/10-tipy-standartnoj-biblioteki-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


`Rust` поставляется со стандартной библиотекой, которая помогает определить набор общих типов, используемых библиотеками и программами `Rust`. Таким образом, две библиотеки могут беспрепятственно работать вместе, поскольку обе они используют один и тот же тип `String`, например.

На самом деле `Rust` содержит несколько слоев стандартной библиотеки: `core`, `alloc` и `std`:

- `core` содержит самые основные типы и функции, которые не зависят от `libc`, распределителя (allocator) или даже наличия операционной системы
- `alloc` включает типы, для которых требуется глобальный распределитель кучи, например `Vec`, `Box` и `Arc`
- встраиваемые приложения, написанные на `Rust`, часто используют только `core` и иногда `alloc`

__Документация__

`Rust` предоставляет замечательную документацию, например:

- описание всех подробностей [циклов](https://doc.rust-lang.org/stable/reference/expressions/loop-expr.html)
- описание примитивных типов, вроде [u8](https://doc.rust-lang.org/stable/std/primitive.u8.html)
- описание типов стандартной библиотеки, таких как [Option](https://doc.rust-lang.org/stable/std/option/enum.Option.html) или [BinaryHeap](https://doc.rust-lang.org/stable/std/collections/struct.BinaryHeap.html)

Мы можем документировать собственный код:

```rust
/// Функция определяет, можно ли первый аргумент делить на второй
///
/// Если вторым аргументом является 0, результатом является `false`
fn is_divisible_by(lhs: u32, rhs: u32) -> bool {
    if rhs == 0 {
        return false;
    }
    lhs % rhs == 0
}
```

Содержимое рассматривается как `Markdown`. Все опубликованные библиотечные крейты (crates) `Rust` автоматически документируются на [docs.rs](https://docs.rs/) с помощью инструмента [rusdoc](https://doc.rust-lang.org/rustdoc/what-is-rustdoc.html).

Чтобы документировать элемент внутри другого элемента (например, внутри модуля), используйте `//!` или `/*! .. */`, называемые "внутренними комментариями документа":

```rust
//! Этот модель содержит функционал, связанный с делением целых чисел
```

- Взгляните на документацию крейта [rand](https://docs.rs/rand)

__Option__

Мы уже несколько раз встречались с `Option`. Он хранит либо некоторое значение `Some(T)`, либо индикатор отсутствия значения `None`. Например, [String::find()](https://doc.rust-lang.org/stable/std/string/struct.String.html#method.find) возвращает `Option<usize>`:

```rust
fn main() {
    let name = "Löwe 老虎 Léopard Gepardi";
    let mut position: Option<usize> = name.find('é');
    println!("find вернул {position:?}");
    assert_eq!(position.unwrap(), 14);
    position = name.find('Z');
    println!("find вернул {position:?}");
    assert_eq!(position.expect("символ не найден"), 0);
}
```

Ремарки:

- `Option` широко используется, не только в стандартной библиотеке
- `unwrap()` либо возвращает значение `Some`, либо паникует. `expect()` похож на `unwrap()`, но принимает сообщение об ошибке
  - мы можем паниковать на `None`, но мы также можем "случайно" забыть проверить `None`
  - `unwrap()`/`expect()` обычно используются для распаковки `Some` в местах, где мы относительно уверены в корректной работе кода. Как правило, в реальных программах `None` обрабатывается лучшим способом
- оптимизация ниши (niche optimization) означает, что `Option<T>` часто занимает столько же памяти, сколько `T`

__Result__

`Result` похож на `Option`, но является индикатором успеха или провала операции, каждый со своим типом. В дженерике `Result<T, E>` `T` используется в варианте `Ok`, а `E` - в варианте `Err`.

```rust
use std::fs::File;
use std::io::Read;

fn main() {
    let file: Result<File, std::io::Error> = File::open("diary.txt");
    match file {
        Ok(mut file) => {
            let mut contents = String::new();
            if let Ok(bytes) = file.read_to_string(&mut contents) {
                println!("{contents}\n({bytes} байт)");
            } else {
                println!("Невозможно прочитать файл");
            }
        }
        Err(err) => {
            println!("Невозможно открыть дневник: {err}");
        }
    }
}
```

Ремарки:

- как и в случае с `Option`, значение `Result` может быть извлечено с помощью `unwrap()`/`expect()`
- `Result` содержит большое количество полезных методов, поэтому рекомендуется ознакомиться с его документацией
- `Result` - это стандартный способ обработки ошибок, о чем мы поговорим в третьей части руководства
- при работе с вводом/выводом тип `Result<T, std::io::Error>` является настолько распространенным, что `std::io` предоставляет специальный `Result`, позволяющий указывать только тип значения `Ok`:

```rust
use std::fs::File;
use std::io::{Read, Result};

// `main()` тоже может возвращать `Result`
fn main() -> Result<()> {
    // Оператор `?` либо распаковывает значение `Ok`, либо распространяет ошибку (возвращает ее вызывающему)
    let mut file = File::open("diary.txt")?;
    let mut contents = String::new();
    let bytes = file.read_to_string(&mut contents)?;
    println!("{contents}\n({bytes} байт)");
    Ok(())
}
```

__String__

[String](https://doc.rust-lang.org/std/string/struct.String.html) - это стандартный выделяемый в куче (heap-allocated) расширяемый (growable) UTF-8 строковый буфер:

```rust
fn main() {
    let mut s1 = String::new();
    s1.push_str("привет");
    println!("s1: длина = {}, емкость = {}", s1.len(), s1.capacity());

    let mut s2 = String::with_capacity(s1.len() + 1);
    s2.push_str(&s1);
    s2.push('!');
    println!("s2: длина = {}, емкость = {}", s2.len(), s2.capacity());

    let s3 = String::from("🇨🇭");
    println!("s3: длина = {}, количество символов = {}", s3.len(), s3.chars().count());
}
```

`String` реализует [`Deref<Target = str>`](https://doc.rust-lang.org/std/string/struct.String.html#deref-methods-str): мы можем вызывать все методы `str` на `String`.

Ремарки:

- `String::new()` возвращает новую пустую строку. Когда заранее известен размер строки, можно использовать `String::with_capacity()`
- `String::len()` возвращает размер `String` в байтах (который может отличаться от количества символов)
- `String::chars()` возвращает итератор по настоящим символам. Обратите внимание, что `char` может отличаться от того, что мы привыкли считать "символом", согласно [кластерам графем](https://docs.rs/unicode-segmentation/latest/unicode_segmentation/struct.Graphemes.html) (grapheme clusters)
- когда мы говорим о строках, мы говорим о `&str` или `String`
- когда тип реализует `Deref<Target = T>`, компилятор позволяет прозрачно вызывать методы `T`
  - `String` реализует `Deref<Target = str>`, что предоставляет ей доступ к методам `str`
  - напишите и сравните `let s3 = s1.deref();` и `let s3 = &*s1;`
- `String` реализован как обертка над вектором байт, многие методы вектора поддерживаются `String`, но с некоторыми ограничениями (гарантиями)
- сравните разные способы индексирования `String`:
  - извлечение символа с помощью `s3.chars().nth(i).unwrap()`, где `i` находится в границах строки и за их пределами
  - извлечение подстроки (среза - slice) с помощью `s3[0..4]`, где диапазон находится в границах символов (character boundaries) и за их пределами

__Vec__

[Vec](https://doc.rust-lang.org/std/vec/struct.Vec.html) - это стандартный расширяемый (resizable) буфер, выделяемый в куче:

```rust
fn main() {
    let mut v1 = Vec::new();
    v1.push(42);
    println!("v1: длина = {}, емкость = {}", v1.len(), v1.capacity());

    let mut v2 = Vec::with_capacity(v1.len() + 1);
    v2.extend(v1.iter());
    v2.push(9999);
    println!("v2: длина = {}, емкость = {}", v2.len(), v2.capacity());

    // Канонический макрос для инициализации вектора с элементами
    let mut v3 = vec![0, 0, 1, 2, 3, 4];

    // Сохраняем только четные элементы
    v3.retain(|x| x % 2 == 0);
    println!("{v3:?}");

    // Удаляем последовательные дубликаты
    v3.dedup();
    println!("{v3:?}");
}
```

`Vec` реализует [`Deref<Target = [T]>`](https://doc.rust-lang.org/std/vec/struct.Vec.html#deref-methods-%5BT%5D): мы можем вызывать методы срезов на `Vec`.

Ремарки:

- `Vec` - это тип коллекции, наряду с `String` и `HashMap`. Данные, которые он содержит, хранятся в куче. Это означает, что размер данных может быть неизвестен во время компиляции. Он может увеличиваться и уменьшаться во время выполнения
- обратите внимание, что `Vec<T>` - это дженерик, но нам не нужно явно определять `T`. `Rust` самостоятельно выводит тип вектора после первого вызова `push()`
- `vec![..]` - это канонический макрос, позволяющий создавать векторы по аналогии с `Vec::new()`, но с начальными элементами
- для индексации вектора можно использовать `[]`, но при выходе за пределы вектора, программа запаникует. Более безопасным доступом к элементам вектора является `get()`, возвращающий `Option`. Метод `pop()` удаляет последний элемент вектора
- `Vec` имеет доступ ко всем методов срезов, о которых мы поговорим в третьей части руководства

__HashMap__

Стандартная хеш-карта с защитой от HashDoS-атак:

```rust
use std::collections::HashMap;

fn main() {
    let mut page_counts = HashMap::new();
    page_counts.insert("Adventures of Huckleberry Finn".to_string(), 207);
    page_counts.insert("Grimms' Fairy Tales".to_string(), 751);
    page_counts.insert("Pride and Prejudice".to_string(), 303);

    if !page_counts.contains_key("Les Misérables") {
        println!(
            "We know about {} books, but not Les Misérables.",
            page_counts.len()
        );
    }

    for book in ["Pride and Prejudice", "Alice's Adventure in Wonderland"] {
        match page_counts.get(book) {
            Some(count) => println!("{book}: {count} pages"),
            None => println!("{book} is unknown."),
        }
    }

    // Метод `entry()` позволяет вставлять значения отсутствующих ключей
    for book in ["Pride and Prejudice", "Alice's Adventure in Wonderland"] {
        let page_count: &mut i32 = page_counts.entry(book.to_string()).or_insert(0);
        *page_count += 1;
    }

    println!("{page_counts:#?}");
}
```

Ремарки:

- `HashMap` не содержится в прелюдии (prelude) и должна импортироваться явно
- попробуйте следующий код. Первая строка проверяет, содержится ли книга в карте и возвращает альтернативное значение при ее отсутствии. Вторая строка вставляет альтернативное значение, если книга не найдена в карте:

```rust
let pc1 = page_counts
    .get("Harry Potter and the Sorcerer's Stone")
    .unwrap_or(&336);
let pc2 = page_counts
    .entry("The Hunger Games".to_string())
    .or_insert(374);
```

- в отличие от `vec!`, `Rust`, к сожалению, не предоставляет макрос `hashmap!`
  - однако, начиная с `Rust 1.56`, `HashMap` реализует [`From<[(K, V); N]>`](https://doc.rust-lang.org/std/collections/hash_map/struct.HashMap.html#impl-From%3C%5B(K,+V);+N%5D%3E-for-HashMap%3CK,+V,+RandomState%3E), позволяющий инициализировать хэш-карту с помощью литерального массива:

```rust
let page_counts = HashMap::from([
  ("Harry Potter and the Sorcerer's Stone".to_string(), 336),
  ("The Hunger Games".to_string(), 374),
]);
```

- `HashMap` может создаваться из любого `Iterator`, возвращающего кортежи `(ключ, значение)`
- в примерах мы избегаем использования `&str` в качестве ключей хэш-карт для простоты. Это возможно, но может привести к проблемам с заимствованием
- рекомендуется внимательно ознакомиться с документацией `HashMap`

__Упражнение: счетчик__

В этом упражнении мы возьмем очень простую структуру данных и сделаем ее универсальной. Она использует `HashMap` для отслеживания того, какие значения были просмотрены и сколько раз появлялось каждое из них.

Первоначальная версия `Counter` жестко запрограммирована для работы только со значениями `u32`. Сделайте структуру и ее методы универсальными для типа отслеживаемого значения, чтобы `Counter` мог работать с любым типом.

Если задание покажется вам слишком легким и вы быстро с ним справитесь, попробуйте использовать метод `entry()`, чтобы вдвое сократить количество поисков хеша, необходимых для реализации метода подсчета.

```rust
use std::collections::HashMap;

// `Counter` считает, сколько раз встретилось каждое значение типа `T`
struct Counter {
    values: HashMap<u32, u64>,
}

impl Counter {
    // Статичный метод создания нового `Counter`
    fn new() -> Self {
        Counter {
            values: HashMap::new(),
        }
    }

    // Метод подсчета появлений определенного значения
    fn count(&mut self, value: u32) {
        if self.values.contains_key(&value) {
            *self.values.get_mut(&value).unwrap() += 1;
        } else {
            self.values.insert(value, 1);
        }
    }

    // Метод возврата количества появлений определенного значения
    fn times_seen(&self, value: u32) -> u64 {
        self.values.get(&value).copied().unwrap_or_default()
    }
}

fn main() {
    let mut ctr = Counter::new();
    ctr.count(13);
    ctr.count(14);
    ctr.count(16);
    ctr.count(14);
    ctr.count(14);
    ctr.count(11);

    for i in 10..20 {
        println!("saw {} values equal to {}", ctr.times_seen(i), i);
    }

    let mut strctr = Counter::new();
    strctr.count("apple");
    strctr.count("orange");
    strctr.count("apple");
    println!("got {} apples", strctr.times_seen("apple"));
}
```

Подсказки:

- общим должен быть только тип ключа
- приступите к реализации `struct Counter<T>` и внимательно изучите подсказку компилятора
- общий тип должен реализовывать 2 встроенных типа: один из прелюдии, другой из `std::hash`

<details>
<summary>Решение:</summary>

```rust
// ...
use std::hash::Hash;

struct Counter<T: Eq + Hash> {
    values: HashMap<T, u64>,
}

impl<T: Eq + Hash> Counter<T> {
    // ...

    fn count(&mut self, value: T) {
        // Дополнительное задание.
        // Здесь также можно использовать `or_insert(0)`
        *self.values.entry(value).or_default() += 1;
    }

    fn times_seen(&self, value: T) -> u64 {
        self.values.get(&value).copied().unwrap_or_default()
    }
}
```

</details>
