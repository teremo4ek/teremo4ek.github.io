---
title: "Пользовательские типы"
description: "Структуры, перечисления, псевдонимы типов, const и static"
date: 2026-05-20T05:00:00Z
weight: 6
image: "/images/rust/06-polzovatelskie-tipy-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Именованные структуры__

`Rust` поддерживает кастомные структуры:

```rust
struct Person {
    name: String,
    age: u8,
}

fn describe(person: &Person) {
    println!("{} is {} years old", person.name, person.age);
}

fn main() {
    let mut peter = Person { name: String::from("Peter"), age: 27 };
    describe(&peter);

    peter.age = 28;
    describe(&peter);

    let name = String::from("Avery");
    let age = 39;
    let avery = Person { name, age };
    describe(&avery);

    let jackie = Person { name: String::from("Jackie"), ..avery };
    describe(&jackie);
}
```

Ремарки:

- тип структуры отдельно определять не нужно
- структуры не могут наследовать друг другу
- для реализации трейта на типе, в котором не нужно хранить никаких значений, можно использовать структуру нулевого размера (zero-sized), например, `struct Foo;`
- если название переменной совпадает с названием поля, то, например, `name: name` можно сократить до `name`
- синтаксис `..avery` позволяет копировать большую часть полей старой структуры в новую структуру. Он должен быть последним элементом

__Кортежные структуры__

Если названия полей неважны, можно использовать кортежную структуру:

```rust
struct Point(i32, i32);

fn main() {
    let p = Point(17, 23);
    println!("({}, {})", p.0, p.1);
}
```

Это часто используется для оберток единичных полей (single-field wrappers), которые называются `newtypes` (новыми типами):

```rust
struct PoundsOfForce(f64);
struct Newtons(f64);

fn compute_thruster_force() -> PoundsOfForce {
    todo!("Ask a rocket scientist at NASA")
}

fn set_thruster_force(force: Newtons) {
    // ...
}

fn main() {
    let force = compute_thruster_force();
    set_thruster_force(force);
}
```

Ремарки:

- `newtype` - отличный способ закодировать дополнительную информацию о значении в примитивном типе, например:
  - число измеряется в определенных единицах (`Newtons`)
  - при создании значение проходит определенную валидацию, которую не нужно каждый раз выполнять вручную: `PhoneNumber(String)` или `OddNumber(u32)`
- пример является тонкой отсылкой к провалу [Mars Climate Orbiter](https://en.wikipedia.org/wiki/Mars_Climate_Orbiter)

__Перечисления__

Ключевое слово `enum` позволяет создать тип, который имеет несколько вариантов:

```rust
#[derive(Debug)]
enum Direction {
    Left,
    Right,
}

#[derive(Debug)]
enum PlayerMove {
    Pass,                        // простой вариант
    Run(Direction),              // кортежный вариант
    Teleport { x: u32, y: u32 }, // структурный вариант
}

fn main() {
    let m: PlayerMove = PlayerMove::Run(Direction::Left);
    println!("On this turn: {:?}", m);
}
```

Ремарки:

- перечисление позволяет собрать набор значений в один тип
- `Direction` - это тип с двумя вариантами: `Direction::Left` и `Direction::Right`
- `PlayerMove` - это тип с тремя вариантами. В дополнение к полезным нагрузкам (payloads) `Rust` будет хранить дискриминант, чтобы во время выполнения знать, какой вариант находится в значении `PlayerMove`
- `Rust` использует минимальное пространство для хранения дискриминанта
  - при необходимости сохраняется целое число наименьшего требуемого размера
  - если разрешенные значения варианта не охватывают все битовые комбинации, для кодирования дискриминанта будут использоваться недопустимые битовые комбинации ("нишевые оптимизации" (niche optimization)). Например, `Option<&u8>` хранит либо указатель на целое число, либо `NULL` для варианта `None`
  - при необходимости дискриминантом можно управлять (например, для обеспечения совместимости с `C`):

```rust
#[repr(u32)]
enum Bar {
    A, // 0
    B = 10000,
    C, // 10001
}

fn main() {
    println!("A: {}", Bar::A as u32);
    println!("B: {}", Bar::B as u32);
    println!("C: {}", Bar::C as u32);
}
```

Без `repr` тип дискриминанта занимает 2 байта, поскольку `10001` соответствует двум байтам.

__Статики и константы__

Статичные (static) и константные (constant) переменные - это 2 способа создания значений с глобальной областью видимости, которые не могут быть перемещены или перераспределены при выполнении программы.

_const_

Константные значения оцениваются во время компиляции и их значения [встраиваются при использовании](https://rust-lang.github.io/rfcs/0246-const-vs-static.html) (inlined upon use):

```rust
const DIGEST_SIZE: usize = 3;
const ZERO: Option<u8> = Some(42);

fn compute_digest(text: &str) -> [u8; DIGEST_SIZE] {
    let mut digest = [ZERO.unwrap_or(0); DIGEST_SIZE];
    for (idx, &b) in text.as_bytes().iter().enumerate() {
        digest[idx % DIGEST_SIZE] = digest[idx % DIGEST_SIZE].wrapping_add(b);
    }
    digest
}

fn main() {
    let digest = compute_digest("hello");
    println!("digest: {digest:?}");
}
```

Только функции, помеченные с помощью `const`, могут вызываться во время компиляции для генерации значений `const`. Но такие функции могут вызываться и во время выполнения.

_static_

Статичные переменные живут на протяжении всего жизненного цикла программы и не могут перемещаться:

```rust
static BANNER: &str = "welcome";

fn main() {
    println!("{BANNER}");
}
```

Значения статичных переменных не встраиваются при использовании и имеют фиксированные локации в памяти. Это может быть полезным для небезопасного и встроенного кода (FFI), но для создания глобальных переменных рекомендуется использовать `const`.

Ремарки:

- `static` обеспечивает идентичность объекта (object identity): адрес в памяти и состояние, как того требуют типы с внутренней изменчивостью, такие как `Mutex<T>`
- константы, которые оцениваются во время выполнения, требуются нечасто, но иногда они могут оказаться полезными, и их использование безопаснее, чем использование статик

__Синонимы типов__

Синоним типа (type alias) создает название для другого типа. Два типа могут использоваться взаимозаменяемо:

```rust
enum CarryableConcreteItem {
    Left,
    Right,
}

type Item = CarryableConcreteItem;

// Синонимы особенно полезны для длинных, сложных типов
use std::cell::RefCell;
use std::sync::{Arc, RwLock};
type PlayerInventory = RwLock<Vec<Arc<RefCell<Item>>>>;
```

__Упражнение: события в лифте__

Ваша задача состоит в том, чтобы создать структуру данных для представления событий в системе управления лифтом. Вам необходимо определить типы и функции для создания различных событий. Используйте `#[derive(Debug)]`, чтобы разрешить форматирование типов с помощью `{:?}`.

Это упражнение требует только создания и заполнения структур данных, чтобы функция `main()` работала без ошибок.

```rust
#[derive(Debug)]
/// Событие, на которое должен реагировать контроллер
enum Event {
    todo!("Добавить необходимые варианты")
}

/// Направление движения
#[derive(Debug)]
enum Direction {
    Up,
    Down,
}

/// Лифт прибыл на определенный этаж
fn car_arrived(floor: i32) -> Event {
    todo!("реализуй меня")
}

/// Двери лифта открылись
fn car_door_opened() -> Event {
    todo!("реализуй меня")
}

/// Двери лифта закрылись
fn car_door_closed() -> Event {
    todo!("реализуй меня")
}

/// В вестибюле лифта на определенном этаже была нажата кнопка направления
fn lobby_call_button_pressed(floor: i32, dir: Direction) -> Event {
    todo!("реализуй меня")
}

/// В кабине лифта была нажата кнопка этажа
fn car_floor_button_pressed(floor: i32) -> Event {
    todo!("реализуй меня")
}

fn main() {
    println!(
        "Пассажир первого этажа нажал кнопку вверх: {:?}",
        lobby_call_button_pressed(0, Direction::Up)
    );
    println!("Лифт прибыл на первый этаж: {:?}", car_arrived(0));
    println!("Двери лифта открылись: {:?}", car_door_opened());
    println!(
        "Пассажир нажал на кнопку третьего этажа: {:?}",
        car_floor_button_pressed(3)
    );
    println!("Двери лифта закрылись: {:?}", car_door_closed());
    println!("Лифт прибыл на третий этаж: {:?}", car_arrived(3));
}
```

<details>
<summary>Решение:</summary>

```rust
#[derive(Debug)]
enum Event {
    /// Была нажата кнопка
    ButtonPressed(Button),
    /// Лифт прибыл на определенный этаж
    CarArrived(Floor),
    /// Двери лифта открылись
    CarDoorOpened,
    /// Двери лифта закрылись
    CarDoorClosed,
}

/// Этаж представлен целым числом
type Floor = i32;

#[derive(Debug)]
enum Direction {
    Up,
    Down,
}

/// Доступная пользователю кнопка
#[derive(Debug)]
enum Button {
    /// Кнопка вызова/направления в вестибюле лифта на определенном этаже
    LobbyCall(Direction, Floor),
    /// Кнопка этажа в кабине лифта
    CarFloor(Floor),
}

fn car_arrived(floor: i32) -> Event {
    Event::CarArrived(floor)
}

fn car_door_opened() -> Event {
    Event::CarDoorOpened
}

fn car_door_closed() -> Event {
    Event::CarDoorClosed
}

fn lobby_call_button_pressed(floor: i32, dir: Direction) -> Event {
    Event::ButtonPressed(Button::LobbyCall(dir, floor))
}

fn car_floor_button_pressed(floor: i32) -> Event {
    Event::ButtonPressed(Button::CarFloor(floor))
}
```

</details>
