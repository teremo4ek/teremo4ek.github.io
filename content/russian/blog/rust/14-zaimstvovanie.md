---
title: "Заимствование"
description: "Правила заимствования, изменяемые ссылки, время жизни ссылок"
date: 2026-05-20T05:00:00Z
weight: 14
image: "/images/rust/14-zaimstvovanie-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Заимствование значения__

Как мы знаем, вместо передачи владения (ownership) значением при вызове функции, можно позволить функции заимствовать (borrow) это значение:

```rust
#[derive(Debug)]
struct Point(i32, i32);

fn add(p1: &Point, p2: &Point) -> Point {
    Point(p1.0 + p2.0, p1.1 + p2.1)
}

fn main() {
    let p1 = Point(3, 4);
    let p2 = Point(10, 20);
    let p3 = add(&p1, &p2);
    println!("{p1:?} + {p2:?} = {p3:?}");
}
```

- Функция `add` заимствует 2 точки (point) и возвращает новую точку
- вызывающий (caller, `main`) сохраняет владение точками

Ремарки:

- возврат значения из функции `add` обходится дешево, поскольку компилятор может исключить операцию копирования
- компилятор `Rust` умеет выполнять оптимизацию возвращаемого значения (return value optimization - RVO)
- в `C++` исключение копирования должно быть определено в спецификации языка, поскольку конструкторы могут иметь побочные эффекты. В `Rust` это не проблема. Если `RVO` не произошло, `Rust` выполняет простое и эффективное копирование `memcpy`

__Проверка заимствований__

Контроллер заимствований (borrow checker) ограничивает способы заимствования значений. Для определенного значения в любое время:

- мы можем иметь одну или более общие/распределенные (shared) ссылки на значение или
- мы можем иметь только одну эксклюзивную/исключительную (exclusive) ссылку на значение

```rust
fn main() {
    let mut a: i32 = 10;
    let b: &i32 = &a;

    {
        let c: &mut i32 = &mut a;
        *c = 20;
    }

    println!("a: {a}");
    println!("b: {b}");
}
```

Ремарки:

- обратите внимание: требование состоит в том, чтобы конфликтующие ссылки не существовали в одно время. Не имеет значения, где ссылка разыменовывается
- код примера не компилируется, поскольку `a` заимствуется как мутабельная (через `c`) и как иммутабельная (через `b`) одновременно
- переместите `println!("b: {b}");` перед областью видимости `c`, чтобы скомпилировать код
- после этого изменения компилятор понимает, что `b` используется только до нового мутабельного заимствования `a`. Это особенность контроллера заимствований, которая называется "нелексическим временем жизни" (non-lexical lifetimes)
- ограничение эксклюзивной ссылки является довольно строгим. `Rust` использует его, чтобы гарантировать отсутствие гонок за данными (data races). `Rust` также использует это ограничение для оптимизации кода. Например, значение общей ссылки можно безопасно кэшировать в регистре на время ее существования
- контроллер заимствований предназначен для использования многих распространенных шаблонов, таких как одновременное получение эксклюзивных ссылок на разные поля в структуре. Но в некоторых ситуациях он не понимает, что мы хотим сделать, и с ним приходится бороться

__Внутренняя изменчивость__

`Rust` предоставляет несколько безопасных способов изменения значения, используя только общую ссылку на это значение. Все они заменяют проверки во время компиляции проверками во время выполнения.

_Cell и RefCell_

[Cell](https://doc.rust-lang.org/std/cell/struct.Cell.html) и [RefCell](https://doc.rust-lang.org/std/cell/struct.RefCell.html) реализуют то, что в `Rust` называется внутренней изменчивостью (interior mutability): мутацией значений в неизменяемом контексте.

`Cell` обычно используется для простых типов, поскольку требует копирования или перемещения значений. Более сложные типы внутреннего пространства обычно используют `RefCell`, который отслеживает общие и эксклюзивные ссылки во время выполнения и паникует, если они используются неправильно.

```rust
use std::cell::RefCell;
use std::rc::Rc;

#[derive(Debug, Default)]
struct Node {
    value: i64,
    children: Vec<Rc<RefCell<Node>>>,
}

impl Node {
    fn new(value: i64) -> Rc<RefCell<Node>> {
        Rc::new(RefCell::new(Node { value, ..Node::default() }))
    }

    fn sum(&self) -> i64 {
        self.value + self.children.iter().map(|c| c.borrow().sum()).sum::<i64>()
    }
}

fn main() {
    let root = Node::new(1);
    root.borrow_mut().children.push(Node::new(5));
    let subtree = Node::new(10);
    subtree.borrow_mut().children.push(Node::new(11));
    subtree.borrow_mut().children.push(Node::new(12));
    root.borrow_mut().children.push(subtree);

    println!("graph: {root:#?}");
    println!("graph sum: {}", root.borrow().sum());
}
```

Ремарки:

- если бы в этом примере мы использовали `Cell` вместо `RefCell`, нам пришлось бы переместить `Node` из `Rc`, чтобы добавить дочерние элементы, а затем вернуть его обратно. Это безопасно, поскольку в ячейке всегда есть одно значение, на которое нет ссылки, но это не эргономично
- для того, чтобы сделать что-то с `Node`, нужно вызвать какой-нибудь метод `RefCell`, обычно `borrow` или `borrow_mut`
- ссылочные циклы могут быть созданы путем добавления `root` в `subtree.children` (не пытайтесь вывести их в терминал)
- для того, чтобы вызвать панику во время выполнения, добавьте `fn inc(&mut self)`, который увеличивает `self.value` и вызывает тот же метод для своих дочерних элементов. Это вызовет панику из-за наличия ссылочного цикла: `thread 'main' panicked at 'already borrowed: BorrowMutError'`

__Упражнение: показатели здоровья__

Вы работаете над внедрением системы мониторинга здоровья. В рамках этого вам необходимо отслеживать показатели здоровья пользователей.

Ваша задача - реализовать метод `visit_doctor` в структуре `User`.

```rust
#![allow(dead_code)]
pub struct User {
    name: String,
    age: u32,
    height: f32,
    visit_count: usize,
    // Опциональное поле
    last_blood_pressure: Option<(u32, u32)>,
}

pub struct Measurements {
    height: f32,
    blood_pressure: (u32, u32),
}

// 'a - это время жизни, мы поговорим об этом в следующем разделе
pub struct HealthReport<'a> {
    patient_name: &'a str,
    visit_count: u32,
    height_change: f32,
    // Опциональное поле
    blood_pressure_change: Option<(i32, i32)>,
}

impl User {
    pub fn new(name: String, age: u32, height: f32) -> Self {
        Self {
            name,
            age,
            height,
            visit_count: 0,
            last_blood_pressure: None,
        }
    }

    pub fn visit_doctor(&mut self, measurements: Measurements) -> HealthReport {
        todo!("Обновляем показатели здоровья пользователя на основе измерений в результате посещения врача")
    }
}

fn main() {
    let bob = User::new(String::from("Bob"), 32, 155.2);
    println!("I'm {} and my age is {}", bob.name, bob.age);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_visit() {
        let mut bob = User::new(String::from("Bob"), 32, 155.2);
        assert_eq!(bob.visit_count, 0);
        let report = bob.visit_doctor(Measurements {
            height: 156.1,
            blood_pressure: (120, 80),
        });
        assert_eq!(report.patient_name, "Bob");
        assert_eq!(report.visit_count, 1);
        assert_eq!(report.blood_pressure_change, None);

        let report = bob.visit_doctor(Measurements {
            height: 156.1,
            blood_pressure: (115, 76),
        });

        assert_eq!(report.visit_count, 2);
        assert_eq!(report.blood_pressure_change, Some((-5, -4)));
    }
}
```

<details>
<summary>Решение:</summary>

```rust
impl User {
    // ...

    pub fn visit_doctor(&mut self, measurements: Measurements) -> HealthReport {
        // Увеличиваем количество посещений врача
        self.visit_count += 1;
        // Показатели кровяного давления из измерений
        let bp = measurements.blood_pressure;
        // Отчет
        let report = HealthReport {
            patient_name: &self.name,
            visit_count: self.visit_count as u32,
            // Изменение роста
            height_change: measurements.height - self.height,
            // Изменение давления.
            // Последнее измерение давления может быть пустым,
            // поэтому выполняется сопоставление с шаблоном
            blood_pressure_change: match self.last_blood_pressure {
                Some(lbp) => {
                    Some((bp.0 as i32 - lbp.0 as i32, bp.1 as i32 - lbp.1 as i32))
                }
                None => None,
            },
        };
        self.height = measurements.height;
        self.last_blood_pressure = Some(bp);
        report
    }
}
```

</details>
