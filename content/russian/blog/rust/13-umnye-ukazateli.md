---
title: "Умные указатели"
description: "Box, Rc, RefCell, умные указатели и их применение"
date: 2026-05-20T05:00:00Z
weight: 13
image: "/images/rust/13-umnye-ukazateli-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__`Box<T>`__

[Box](https://doc.rust-lang.org/std/boxed/struct.Box.html) - это собственный указатель на данные в куче:

```rust
fn main() {
    let five = Box::new(5);
    println!("пять: {}", *five);
}
```

`Box<T>` реализует `Deref<Target = T>`: мы можем [вызывать методы `T` прямо на `Box<T>`](https://doc.rust-lang.org/std/ops/trait.Deref.html#more-on-deref-coercion).

Рекурсивные типы или типы динамического размера должны использовать `Box`:

```rust
#[derive(Debug)]
enum List<T> {
    // Непустой список: первый элемент и остальная часть списка
    Element(T, Box<List<T>>),
    // Пустой список
    Nil,
}

fn main() {
    let list: List<i32> =
        List::Element(1, Box::new(List::Element(2, Box::new(List::Nil))));
    println!("{list:?}");
}
```

<img src="https://habrastorage.org/webt/y_/mi/gm/y_migm2n3g0zfpdq8v7nc0ujmxm.png" />
<br />

Ремарки:

- `Box` похож на `std::unique_ptr` в `C++`, за исключением того, что он не может иметь значение `NULL`
- `Box` может быть полезным, когда
  - у нас есть тип, размер которого неизвестен во время компиляции, а компилятору `Rust` нужен точный размер
  - мы хотим передать владение большого количества данных. Вместо копирования большого количества данных в стеке, мы храним данные в куче в `Box` и перемещаем только указатель
- если мы попытаемся внедрить `List` прямо в `List` без использования `Box`, компилятор не сможет вычислить точный размер структуры в памяти (`List` будет иметь бесконечный размер)
- `Box` решает эту проблему, поскольку он имеет такой же размер, что обычный указатель и просто указывает на следующий элемент списка в куче
- удалите `Box` из определения `List` и изучите ошибку компилятора

_Нишевая оптимизация_

```rust
#[derive(Debug)]
enum List<T> {
    Element(T, Box<List<T>>),
    Nil,
}

fn main() {
    let list: List<i32> =
        List::Element(1, Box::new(List::Element(2, Box::new(List::Nil))));
    println!("{list:?}");
}
```

`Box` не может быть пустым, поэтому указатель всегда является валидным и не может иметь значение `NULL`. Это позволяет компилятору оптимизировать слой памяти:

<img src="https://habrastorage.org/webt/1h/nk/vy/1hnkvyqurluuqpnyhm2zk68jax0.png" />
<br />

__Rc__

[Rc](https://doc.rust-lang.org/std/rc/struct.Rc.html) - это общий указатель с подсчетом ссылок. Он используется, когда нужно сослаться на одни и те же данные из нескольких мест:

```rust
use std::rc::Rc;

fn main() {
    let a = Rc::new(10);
    let b = Rc::clone(&a);

    println!("a: {a}");
    println!("b: {b}");
}
```

- В многопоточных контекстах следует использовать [Arc](https://google.github.io/comprehensive-rust/concurrency/shared_state/arc.html) и [Mutex](https://doc.rust-lang.org/std/sync/struct.Mutex.html)
- мы можем понизить общий указатель до слабого указателя ([Weak](https://doc.rust-lang.org/std/rc/struct.Weak.html)) для создания циклов, которые будут правильно уничтожены в свое время

Ремарки:

- счетчик `Rc` гарантирует, что содержащееся в нем значение действительно до тех пор, пока существуют ссылки на него
- `Rc` в `Rust` похож на `std::shared_ptr` в `C++`
- `Rc::clone` обходится дешево: он создает указатель на одно и то же место в памяти и увеличивает счетчик ссылок. Он не создает глубоких клонов, и его обычно можно игнорировать при поиске в коде проблем с производительностью
- `make_mut` фактически клонирует внутреннее значение при необходимости ("клонирование при записи" - clone-on-write) и возвращает изменяемую ссылку
- `Rc::strong_count` используется для определения количества активных ссылок
- `Rc::downgrade` (вероятно, в сочетании с `RefCell`) позволяет создавать объекты со слабым подсчетом ссылок для создания циклов, которые будут правильно удалены в будущем

__Упражнение: двоичное дерево__

Бинарное дерево (binary tree) - это древовидная структура данных, в которой каждый узел имеет 2 дочерних элемента (левый и правый). Мы создадим дерево, в котором каждый узел хранит значение. Для данного узла `N` все узлы в левом поддереве `N` содержат меньшие значения, а все узлы в правом поддереве `N` - большие значения.

Если задание покажется вам легким и вы быстро с ним справитесь, попробуйте реализовать итератор по дереву, который будет возвращать все значения по порядку.

```rust
// Узел дерева
#[derive(Debug)]
struct Node<T: Ord> {
    value: T,
    left: Subtree<T>,
    right: Subtree<T>,
}

// Поддерево, которое может быть пустым
#[derive(Debug)]
struct Subtree<T: Ord>(Option<Box<Node<T>>>);

// Контейнер, хранящий набор значений с помощью двоичного дерева.
// Значение сохраняется только один раз, независимо от того, сколько раз оно добавляется
#[derive(Debug)]
pub struct BinaryTree<T: Ord> {
    root: Subtree<T>,
}

impl<T: Ord> BinaryTree<T> {
    fn new() -> Self {
        todo!("реализуй меня")
    }

    fn insert(&mut self, value: T) {
        todo!("реализуй меня")
    }

    fn has(&self, value: &T) -> bool {
        todo!("реализуй меня")
    }

    fn len(&self) -> usize {
        todo!("реализуй меня")
    }
}

impl<T: Ord> Subtree<T> {
    fn new() -> Self {
        todo!("реализуй меня")
    }

    fn insert(&mut self, value: T) {
        todo!("реализуй меня")
    }

    fn has(&self, value: &T) -> bool {
        todo!("реализуй меня")
    }

    fn len(&self) -> usize {
        todo!("реализуй меня")
    }
}

impl<T: Ord> Node<T> {
    fn new(value: T) -> Self {
        todo!("реализуй меня")
    }
}

fn main() {
    let mut tree = BinaryTree::new();
    tree.insert("foo");
    assert_eq!(tree.len(), 1);
    tree.insert("bar");
    assert!(tree.has(&"foo"));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn len() {
        let mut tree = BinaryTree::new();
        assert_eq!(tree.len(), 0);
        tree.insert(2);
        assert_eq!(tree.len(), 1);
        tree.insert(1);
        assert_eq!(tree.len(), 2);
        tree.insert(2); // дубликат
        assert_eq!(tree.len(), 2);
    }

    #[test]
    fn has() {
        let mut tree = BinaryTree::new();
        fn check_has(tree: &BinaryTree<i32>, exp: &[bool]) {
            let got: Vec<bool> =
                (0..exp.len()).map(|i| tree.has(&(i as i32))).collect();
            assert_eq!(&got, exp);
        }

        check_has(&tree, &[false, false, false, false, false]);
        tree.insert(0);
        check_has(&tree, &[true, false, false, false, false]);
        tree.insert(4);
        check_has(&tree, &[true, false, false, false, true]);
        tree.insert(4);
        check_has(&tree, &[true, false, false, false, true]);
        tree.insert(3);
        check_has(&tree, &[true, false, false, true, true]);
    }

    #[test]
    fn unbalanced() {
        let mut tree = BinaryTree::new();
        for i in 0..100 {
            tree.insert(i);
        }
        assert_eq!(tree.len(), 100);
        assert!(tree.has(&50));
    }
}
```

Подсказка: для сопоставления с шаблоном при сравнении значений следует использовать `std::cmp::Ordering`.

<details>
<summary>Решение:</summary>

```rust
impl<T: Ord> BinaryTree<T> {
    fn new() -> Self {
        Self { root: Subtree::new() }
    }

    fn insert(&mut self, value: T) {
        self.root.insert(value);
    }

    fn has(&self, value: &T) -> bool {
        self.root.has(value)
    }

    fn len(&self) -> usize {
        self.root.len()
    }
}

impl<T: Ord> Subtree<T> {
    fn new() -> Self {
        Self(None)
    }

    fn insert(&mut self, value: T) {
        match &mut self.0 {
            None => self.0 = Some(Box::new(Node::new(value))),
            Some(n) => match value.cmp(&n.value) {
                Ordering::Less => n.left.insert(value),
                Ordering::Equal => {}
                Ordering::Greater => n.right.insert(value),
            },
        }
    }

    fn has(&self, value: &T) -> bool {
        match &self.0 {
            None => false,
            Some(n) => match value.cmp(&n.value) {
                Ordering::Less => n.left.has(value),
                Ordering::Equal => true,
                Ordering::Greater => n.right.has(value),
            },
        }
    }

    fn len(&self) -> usize {
        match &self.0 {
            None => 0,
            Some(n) => 1 + n.left.len() + n.right.len(),
        }
    }
}

impl<T: Ord> Node<T> {
    fn new(value: T) -> Self {
        Self { value, left: Subtree::new(), right: Subtree::new() }
    }
}
```

</details>
