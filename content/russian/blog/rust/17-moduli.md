---
title: "Модули"
description: "Модули, crate, use, pub, структура проекта"
date: 2026-05-20T05:00:00Z
weight: 17
image: "/images/rust/17-moduli-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Модули__

Мы видели, как блоки `impl` позволяют нам использовать функции пространства имен (namespace) для типа.

Аналогично, `mod` позволяет нам использовать типы и функции пространства имен:

```rust
mod foo {
    pub fn do_something() {
        println!("в модуле foo");
    }
}

mod bar {
    pub fn do_something() {
        println!("в модуле bar");
    }
}

fn main() {
    foo::do_something();
    bar::do_something();
}
```

Ремарки:

- пакеты (packages) предоставляют функционал и включают файл `Cargo.toml`, описывающий сборку из нескольких крейтов
- крейты (crates) - это дерево модулей, где бинарный крейт является исполняемым файлом, а библиотечный крейт компилируется в библиотеку
- модули определяют организацию и область видимости кода

__Иерархия файловой системы__

Если опустить содержимое модуля, `Rust` будет искать его в другом файле:

```rust
mod garden;
```

Это сообщает `Rust`, что содержимое модуля `Garden` находится по адресу `src/garden.rs`. Аналогично, модуль `Garden::vegetables` следует искать по адресу `src/garden/vegetables.rs`.

Корневой `crate` находится в:

- `src/lib.rs` (для библиотечного крейта)
- `src/main.rs` (для бинарного крейта)

Модули, определенные в файлах, можно документировать с помощью "внутренних комментариев документа". Они документируют элемент, который их содержит - в данном случае модуль.

```rust
//! This module implements the garden, including a highly performant germination
//! implementation.

// Re-export types from this module.
pub use garden::Garden;
pub use seeds::SeedPacket;

/// Sow the given seed packets.
pub fn sow(seeds: Vec<SeedPacket>) {
    todo!()
}

/// Harvest the produce in the garden that is ready.
pub fn harvest(garden: &mut Garden) {
    todo!()
}
```

Ремарки:

- до `Rust 2018` модули должны были находиться в `module/mod.rs` вместо `module.rs`, и это по-прежнему работает
- основная причина представления `filename.rs` в качестве альтернативы `filename/mod.rs` заключается в том, что при большом количестве файлов `mod.rs` становится сложно в них разбираться
- при более глубокой вложенности можно использовать директории, даже если основной модуль является файлом:

```
src/
├── main.rs
├── top_module.rs
└── top_module/
    └── sub_module.rs
```

- место поиска модулей может быть изменено с помощью директивы компилятора:

```rust
#[path = "some/path.rs"]
mod some_module;
```

Это может быть полезным, например, когда мы хотим поместить тесты для модуля в файл с именем `some_module_test.rs`.

__Видимость__

Модули являются приватными/закрытыми:

- элементы модулей являются приватными по умолчанию (скрывают детали своей реализации)
- родители и сиблинги всегда являются видимыми (для элементов модулей)
- если элемент видим в модуле `foo`, он видим всем потомкам `foo`

```rust
mod outer {
    fn private() {
        println!("outer::private");
    }

    pub fn public() {
        println!("outer::public");
    }

    mod inner {
        fn private() {
            println!("outer::inner::private");
        }

        pub fn public() {
            println!("outer::inner::public");
            super::private();
        }
    }
}

fn main() {
    outer::public();
}
```

Ремарки:

- для того, чтобы сделать модуль публичным/открытым, используется ключевое слово `pub`
- существуют [продвинутые спецификаторы `pub`](https://doc.rust-lang.org/reference/visibility-and-privacy.html#pubin-path-pubcrate-pubsuper-and-pubself), позволяющие ограничивать область публичной видимости

__use, super, self__

Модуль может импортировать элементы другого модуля в свою область видимости с помощью ключевого слова `use`. В начале каждого модуля можно увидеть что-то вроде этого:

```rust
use std::collections::HashSet;
use std::process::abort;
```

_Пути_

Путь (path) разрешается следующим образом:

1. Как относительный путь:
   - `foo` или `self::foo` ссылается на `foo` в текущем модуле
   - `super::foo` ссылается на `foo` в родительском модуле
2. Как абсолютный путь:
   - `crate:foo` ссылается на `foo` в корне текущего крейта
   - `bar::foo` ссылается на `foo` в крейте `bar`

Ремарки:

- распространенной практикой является повторный экспорт элементов модулей. Например, корневой файл `lib.rs` может содержать:

```rust
mod storage;

pub use storage::disk::DiskStorage;
pub use storage::network::NetworkStorage;
```

Это сделает `DiskStorage` и `NetworkStorage` доступными другим крейтам по короткому пути.

- в основном, необходимо `use` (использовать) только элементы, которые используются в модуле. Однако для того, чтобы вызывать методы трейта, он должен находиться в области видимости, даже если тип, реализующий этот трейт, уже находится в ней. Например, чтобы использовать метод `read_to_string` для типа, реализующего трейт `Read`, необходимо `use std::io::Read`
- в операторе `use` может использоваться подстановочный знак: `use std::io::*`. Делать так не рекомендуется, поскольку неясно, какие элементы импортируются, и эти элементы могут измениться со временем

__Упражнение: модули для библиотеки пользовательского интерфейса__

В этом упражнении вы реорганизуете код "Библиотеки графического интерфейса" из раздела "Методы и трейты" в набор модулей. Обычно каждый тип или набор тесно связанных типов помещают в отдельный модуль, поэтому каждый тип виджета должен иметь свой собственный модуль.

Код:

```rust
pub trait Widget {
    fn width(&self) -> usize;

    fn draw_into(&self, buffer: &mut dyn std::fmt::Write);

    fn draw(&self) {
        let mut buffer = String::new();
        self.draw_into(&mut buffer);
        println!("{buffer}");
    }
}

pub struct Label {
    label: String,
}

impl Label {
    fn new(label: &str) -> Label {
        Label { label: label.to_owned() }
    }
}

pub struct Button {
    label: Label,
}

impl Button {
    fn new(label: &str) -> Button {
        Button { label: Label::new(label) }
    }
}

pub struct Window {
    title: String,
    widgets: Vec<Box<dyn Widget>>,
}

impl Window {
    fn new(title: &str) -> Window {
        Window { title: title.to_owned(), widgets: Vec::new() }
    }

    fn add_widget(&mut self, widget: Box<dyn Widget>) {
        self.widgets.push(widget);
    }

    fn inner_width(&self) -> usize {
        std::cmp::max(
            self.title.chars().count(),
            self.widgets.iter().map(|w| w.width()).max().unwrap_or(0),
        )
    }
}

impl Widget for Window {
    fn width(&self) -> usize {
        self.inner_width() + 4
    }

    fn draw_into(&self, buffer: &mut dyn std::fmt::Write) {
        let mut inner = String::new();
        for widget in &self.widgets {
            widget.draw_into(&mut inner);
        }

        let inner_width = self.inner_width();

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
        self.label.width() + 4
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

fn main() {
    let mut window = Window::new("Rust GUI Demo 1.23");
    window.add_widget(Box::new(Label::new("This is a small text GUI demo.")));
    window.add_widget(Box::new(Button::new("Click me!")));
    window.draw();
}
```

Упражнение можно начать с выполнения следующих команд:

```bash
cargo init gui-modules
cd gui-modules
cargo run
```

Отредактируйте файл `src/main.rs`, добавив в него инструкции `mod`, и создайте необходимые файлы в директории `src`.

<details>
<summary>Решение:</summary>

```
src
├── main.rs
├── widgets
│   ├── button.rs
│   ├── label.rs
│   └── window.rs
└── widgets.rs
```

```rust
// src/widgets.rs
mod button;
mod label;
mod window;

pub trait Widget {
    fn width(&self) -> usize;

    fn draw_into(&self, buffer: &mut dyn std::fmt::Write);

    fn draw(&self) {
        let mut buffer = String::new();
        self.draw_into(&mut buffer);
        println!("{buffer}");
    }
}

pub use button::Button;
pub use label::Label;
pub use window::Window;
```

```rust
// src/widgets/label.rs
use super::Widget;

pub struct Label {
    label: String,
}

impl Label {
    pub fn new(label: &str) -> Label {
        Label { label: label.to_owned() }
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

```rust
// src/widgets/button.rs
use super::{Label, Widget};

pub struct Button {
    label: Label,
}

impl Button {
    pub fn new(label: &str) -> Button {
        Button { label: Label::new(label) }
    }
}

impl Widget for Button {
    fn width(&self) -> usize {
        self.label.width() + 4
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
```

```rust
// src/widgets/window.rs
use super::Widget;

pub struct Window {
    title: String,
    widgets: Vec<Box<dyn Widget>>,
}

impl Window {
    pub fn new(title: &str) -> Window {
        Window { title: title.to_owned(), widgets: Vec::new() }
    }

    pub fn add_widget(&mut self, widget: Box<dyn Widget>) {
        self.widgets.push(widget);
    }

    fn inner_width(&self) -> usize {
        std::cmp::max(
            self.title.chars().count(),
            self.widgets.iter().map(|w| w.width()).max().unwrap_or(0),
        )
    }
}

impl Widget for Window {
    fn width(&self) -> usize {
        self.inner_width() + 4
    }

    fn draw_into(&self, buffer: &mut dyn std::fmt::Write) {
        let mut inner = String::new();
        for widget in &self.widgets {
            widget.draw_into(&mut inner);
        }

        let inner_width = self.inner_width();

        writeln!(buffer, "+-{:-<inner_width$}-+", "").unwrap();
        writeln!(buffer, "| {:^inner_width$} |", &self.title).unwrap();
        writeln!(buffer, "+={:=<inner_width$}=+", "").unwrap();
        for line in inner.lines() {
            writeln!(buffer, "| {:inner_width$} |", line).unwrap();
        }
        writeln!(buffer, "+-{:-<inner_width$}-+", "").unwrap();
    }
}
```

```rust
// src/main.rs
mod widgets;

use widgets::Widget;

fn main() {
    let mut window = widgets::Window::new("Rust GUI Demo 1.23");
    window
        .add_widget(Box::new(widgets::Label::new("This is a small text GUI demo.")));
    window.add_widget(Box::new(widgets::Button::new("Click me!")));
    window.draw();
}
```

</details>
