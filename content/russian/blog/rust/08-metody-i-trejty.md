---
title: "Методы и трейты"
description: "Методы, трейты, реализация трейтов, трейт-объекты"
date: 2026-05-20T05:00:00Z
weight: 8
image: "/images/rust/08-metody-i-trejty-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Методы__

`Rust` позволяет привязывать функции к типам (такие функции называются ассоциированными - методы экземпляров в других языках). Это делается с помощью блока `impl`:

```rust
#[derive(Debug)]
struct Race {
    name: String,
    laps: Vec<i32>,
}

impl Race {
    // Нет получателя, статичный метод
    fn new(name: &str) -> Self {
        Self { name: String::from(name), laps: Vec::new() }
    }

    // Эксклюзивное заимствование (exclusive borrowing), допускающее чтение и запись в `self`
    fn add_lap(&mut self, lap: i32) {
        self.laps.push(lap);
    }

    // Общее, доступное только для чтение заимствование (shared borrowing) `self`
    fn print_laps(&self) {
        println!("Записано время {} кругов для {}:", self.laps.len(), self.name);
        for (idx, lap) in self.laps.iter().enumerate() {
            println!("Круг {idx}: {lap} секунд");
        }
    }

    // Эксклюзивное владение (exclusive ownership) `self`
    fn finish(self) {
        let total: i32 = self.laps.iter().sum();
        println!("Гонка {} закончена, общее время: {}", self.name, total);
    }
}

fn main() {
    let mut race = Race::new("Monaco Grand Prix");
    race.add_lap(70);
    race.add_lap(68);
    race.print_laps();
    race.add_lap(71);
    race.print_laps();
    race.finish();
    // race.add_lap(42);
}
```

Аргументы `self` определяют "получателя" (receiver) - объект, на котором реализуется метод. Получатели могут быть следующими:

- `&self` - заимствует объект у вызывающего с помощью общей иммутабельной ссылки. После этого объект может быть повторно использован
- `&mut self` - заимствует объект у вызывающего с помощью уникальной мутабельной ссылки. После этого объект может быть повторно использован
- `self` - принимает владение объектом и перемещает его от вызывающего. Метод становится владельцем объекта. Объект удаляется (освобождается) после того, как метод вернул значение. Полное владение не означает автоматической мутабельности
- `mut self` - аналогично `self`, но метод может модифицировать объект
- нет получателя - такой метод становится статичным. Обычно используется для создания конструкторов, которые по соглашению вызываются с помощью `new()`

Ремарки:

- методы отличаются от функций следующим:
  - методы вызываются на экземпляре типа (такого как структура или перечисление), их первый параметр - сам экземпляр (`self`)
  - методы позволяют держать код реализации функционала в одном месте, что способствует лучшей организации кода
- особенности использования ключевого слова `self`:
  - `self` является сокращением для `self: Self`, вместо `Self` может использоваться название структуры, например, `Race`
  - таким образом, `Self` - это синоним реализуемого (`impl`) типа и может быть использован в любом месте внутри блока
  - `self` используется как другие структуры, для доступа к его отдельным полям может использоваться точечная нотация
  - для демонстрации разницы между `&self` и `self` попробуйте запустить `finish()` дважды
  - существуют также [специальные обертки типов](https://doc.rust-lang.org/reference/special-types-and-traits.html), которые могут использоваться в качестве типов получателя, например, `Box<Self>`

__Трейты__

`Rust` позволяет создавать абстрактные типы с помощью трейтов (traits). Они похожи на интерфейсы в других языках программирования:

```rust
struct Dog {
    name: String,
    age: i8,
}
struct Cat {
    lives: i8,
}

trait Pet {
    fn talk(&self) -> String;

    fn greet(&self) {
        println!("Какая милаха! Как тебя зовут? {}", self.talk());
    }
}

impl Pet for Dog {
    fn talk(&self) -> String {
        format!("Гав, меня зовут {}!", self.name)
    }
}

impl Pet for Cat {
    fn talk(&self) -> String {
        String::from("Мау!")
    }
}

fn main() {
    let captain_floof = Cat { lives: 9 };
    let fido = Dog { name: String::from("Фидо"), age: 5 };

    captain_floof.greet();
    fido.greet();
}
```

Ремарки:

- трейт определяет методы, которые должен предоставлять тип для реализации этого трейта
- трейты реализуются в блоке `impl <trait> for <type> { .. }`
- трейты могут определять как дефолтные методы, так и методы, которые пользователь должен реализовать самостоятельно. Дефолтные методы могут полагаться на пользовательские: `greet()` имеет реализацию по умолчанию и зависит от `talk()`

__Автоматическая реализация трейтов__

Встроенные/стандартные трейты могут быть реализованы на кастомных типах автоматически:

```rust
#[derive(Debug, Clone, Default)]
struct Player {
    name: String,
    strength: u8,
    hit_points: u8,
}

fn main() {
    let p1 = Player::default(); // трейт `Default` добавляет конструктор `default()`.
    let mut p2 = p1.clone(); // трейт `Clone` добавляет метод `clone()`
    p2.name = String::from("EldurScrollz");
    // Трейт `Debug` добавляет поддержку вывода в терминал с помощью `{:?}`.
    println!("{:?} vs. {:?}", p1, p2);
}
```

Автоматическая реализация выполняется с помощью макросов, многие крейты предоставляют макросы для добавления полезного функционала. Например, крейт [serde](https://crates.io/crates/serde) предоставляет автоматическую реализацию сериализации с помощью `#[derive(Serialize)]`.

__Трейт-объекты__

Трейт-объекты (trait objects) позволяют хранить значения разных типов, например, в коллекции:

```rust
struct Dog {
    name: String,
    age: i8,
}
struct Cat {
    lives: i8,
}

trait Pet {
    fn talk(&self) -> String;
}

impl Pet for Dog {
    fn talk(&self) -> String {
        format!("Гав, меня зовут {}!", self.name)
    }
}

impl Pet for Cat {
    fn talk(&self) -> String {
        String::from("Мау!")
    }
}

fn main() {
    // Трейт-объект, который может содержать значение любого типа, реализующего трейт `Pet`
    let pets: Vec<Box<dyn Pet>> = vec![
        Box::new(Cat { lives: 9 }),
        Box::new(Dog { name: String::from("Фидо"), age: 5 }),
    ];
    for pet in pets {
        println!("Привет, кто ты? {}", pet.talk());
    }
}
```

Память после выделения `pets`:

<img src="https://habrastorage.org/webt/cf/ri/s6/cfris6v-ltwp4tskiepa4rghw9e.png" />
<br />

Ремарки:

- типы, реализующие определенный трейт, могут иметь разный размер. Это делает возможным такие вещи, как `Vec<dyn Pet>` в примере
- `dyn Pet` - это способ сообщить компилятору о типе динамического размера, который реализует `Pet`
- в примере `pets` выделяются в стеке (stack), а вектор - в куче (heap). 2 элемента вектора являются жирными указателями (fat pointers):
  - жирный указатель - это указатель двойной ширины. Он состоит из двух компонентов: указателя на реальный объект и указателя на [таблицу виртуальных методов](https://en.wikipedia.org/wiki/Virtual_method_table) (vtable) для реализации `Pet` этого конкретного объекта
  - данными для `Dog` являются `name` и `age`. `Cat` имеет поле `lives`
- сравните эти выводы:

```rust
println!("{} {}", std::mem::size_of::<Dog>(), std::mem::size_of::<Cat>());
println!("{} {}", std::mem::size_of::<&Dog>(), std::mem::size_of::<&Cat>());
println!("{}", std::mem::size_of::<&dyn Pet>());
println!("{}", std::mem::size_of::<Box<dyn Pet>>());
```

__Упражнение: библиотека GUI__

Спроектируем классическую библиотеку GUI (graphical user interface - графический пользовательский интерфейс). Для простоты реализуем только его рисование - вывод в терминал в виде текста.

В нашей библиотеке будет несколько виджетов:

- `Window` - имеет `title` и содержит другие виджеты
- `Button` - имеет `label`. В реальной библиотеке кнопка также будет принимать обработчик ее нажатия
- `Label` - имеет `label`

Виджеты реализуют трейт `Widget`.

Напишите методы `draw_into()` для реализации трейта `Widget`.

```rust
pub trait Widget {
    // Натуральная ширина `self`.
    fn width(&self) -> usize;

    // Рисуем/записываем виджет в буфер
    fn draw_into(&self, buffer: &mut dyn std::fmt::Write);

    // Рисуем виджет в стандартный вывод
    fn draw(&self) {
        let mut buffer = String::new();
        self.draw_into(&mut buffer);
        println!("{buffer}");
    }
}

// Подпись может состоять из нескольких строк
pub struct Label {
    label: String,
}

impl Label {
    // Конструктор подписи
    fn new(label: &str) -> Label {
        Label { label: label.to_owned() }
    }
}

pub struct Button {
    label: Label,
}

impl Button {
    // Конструктор кнопки
    fn new(label: &str) -> Button {
        Button { label: Label::new(label) }
    }
}

pub struct Window {
    title: String,
    widgets: Vec<Box<dyn Widget>>,
}

impl Window {
    // Конструктор окна
    fn new(title: &str) -> Window {
        Window { title: title.to_owned(), widgets: Vec::new() }
    }

    // Метод добавления виджета
    fn add_widget(&mut self, widget: Box<dyn Widget>) {
        self.widgets.push(widget);
    }

    // Метод получения максимальной ширины
    fn inner_width(&self) -> usize {
        std::cmp::max(
            self.title.chars().count(),
            self.widgets.iter().map(|w| w.width()).max().unwrap_or(0),
        )
    }
}

impl Widget for Window {
    todo!("реализуй меня")
}
impl Widget for Button {
    todo!("реализуй меня")
}
impl Widget for Label {
    todo!("реализуй меня")
}

fn main() {
    let mut window = Window::new("Rust GUI Demo 1.23");
    window.add_widget(Box::new(Label::new("This is a small text GUI demo.")));
    window.add_widget(Box::new(Button::new("Click me!")));
    window.draw();
}
```

Вывод программы может быть очень простым:

```rust
========
Rust GUI Demo 1.23
========

This is a small text GUI demo.

| Click me! |
```

Или же можно воспользоваться операторами форматирования [заполнения/выравнивания](https://doc.rust-lang.org/std/fmt/index.html#fillalignment) для выравнивания текста. Вот как можно управлять выравниванием текста с помощью разных символов (например, `/`):

```rust
fn main() {
    let width = 10;
    println!("слева:     |{:/<width$}|", "foo");
    println!("по центру: |{:/^width$}|", "foo");
    println!("справа:    |{:/>width$}|", "foo");
}
```

Эти приемы позволяют сделать вывод программы таким:

```rust
+--------------------------------+
|       Rust GUI Demo 1.23       |
+================================+
| This is a small text GUI demo. |
| +-------------+                |
| |  Click me!  |                |
| +-------------+                |
+--------------------------------+
```

<details>
<summary>Решение:</summary>

```rust
impl Widget for Window {
    fn width(&self) -> usize {
        // Добавляем к максимальной ширине 4 для отступов и границ
        // (по одному отступу и границе с каждой стороны)
        self.inner_width() + 4
    }

    fn draw_into(&self, buffer: &mut dyn std::fmt::Write) {
        let mut inner = String::new();
        for widget in &self.widgets {
            widget.draw_into(&mut inner);
        }

        let inner_width = self.inner_width();

        // TODO: после изучения обработки ошибок, можно сделать так,
        // чтобы метод `draw_into()` возвращал `Result<(), std::fmt::Error>`
        // и использовать здесь оператор ? вместо `unwrap()`
        writeln!(buffer, "+-{:-<inner_width$}-+", "").unwrap();
        writeln!(buffer, "| {:^inner_width$} |", &self.title).unwrap();
        writeln!(buffer, "+={:=<inner_width$}=+", "").unwrap();
        for line in inner.lines() {
            writeln!(buffer, "| {:inner_width$} |", line).unwrap();
        }
        writeln!(buffer, "+-{:-<inner_width$}-+", "").unwrap();
    }
}

impl Widget for Button {
    fn width(&self) -> usize {
        self.label.width() + 4 // добавляем немного отступов (по 2 с каждой стороны)
    }

    fn draw_into(&self, buffer: &mut dyn std::fmt::Write) {
        let width = self.width();
        let mut label = String::new();
        self.label.draw_into(&mut label);

        writeln!(buffer, "+{:-<width$}+", "").unwrap();
        for line in label.lines() {
            writeln!(buffer, "|{:^width$}|", &line).unwrap();
        }
        writeln!(buffer, "+{:-<width$}+", "").unwrap();
    }
}

impl Widget for Label {
    fn width(&self) -> usize {
        self.label.lines().map(|line| line.chars().count()).max().unwrap_or(0)
    }

    fn draw_into(&self, buffer: &mut dyn std::fmt::Write) {
        writeln!(buffer, "{}", &self.label).unwrap();
    }
}
```

</details>
