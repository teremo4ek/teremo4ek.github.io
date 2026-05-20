---
title: "Итераторы"
description: "Протокол итераторов, IntoIterator, адаптеры и потребители"
date: 2026-05-20T05:00:00Z
weight: 16
image: "/images/rust/16-iteratory-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Iterator__

Трейт [Iterator](https://doc.rust-lang.org/std/iter/trait.Iterator.html) позволяет перебирать значения коллекции. Он требует реализации метода `next` и предоставляет большое количество полезных методов. Многие типы стандартной библиотеки реализуют `Iterator`, и мы также можем его реализовывать на собственных типах:

```rust
struct Fibonacci {
    curr: u32,
    next: u32,
}

impl Iterator for Fibonacci {
    type Item = u32;

    fn next(&mut self) -> Option<Self::Item> {
        let new_next = self.curr + self.next;
        self.curr = self.next;
        self.next = new_next;
        Some(self.curr)
    }
}

fn main() {
    let fib = Fibonacci { curr: 0, next: 1 };
    for (i, n) in fib.enumerate().take(5) {
        println!("fib({i}): {n}");
    }
}
```

Ремарки:

- трейт `Iterator` реализует много популярных операций функционального программирования над коллекциями (`map`, `filter`, `reduce` и т.д.). В `Rust` эти функции должны создавать код, столь же эффективный, как и эквивалентные императивные реализации
- `IntoIterator` - это трейт, обеспечивающий работу цикла `for`. Он реализуется типами коллекций, такими как `Vec<T>`, и ссылками на них, такими как `&Vec<T>` и `&[T]`. Диапазоны (ranges) также реализуют этот трейт. Вот почему мы можем перебирать элементы вектора с помощью `for i in some_vec { .. }`, но `some_vec.next()` отсутствует

__IntoIterator__

Трейт `Iterator` сообщает, как выполнять итерацию после создания итератора. Трейт [IntoIterator](https://doc.rust-lang.org/std/iter/trait.IntoIterator.html) определяет, как создать итератор для типа. Он автоматически используется циклом `for`.

```rust
struct Grid {
    x_coords: Vec<u32>,
    y_coords: Vec<u32>,
}

impl IntoIterator for Grid {
    type Item = (u32, u32);
    type IntoIter = GridIter;

    fn into_iter(self) -> GridIter {
        GridIter { grid: self, i: 0, j: 0 }
    }
}

struct GridIter {
    grid: Grid,
    i: usize,
    j: usize,
}

impl Iterator for GridIter {
    type Item = (u32, u32);

    fn next(&mut self) -> Option<(u32, u32)> {
        if self.i >= self.grid.x_coords.len() {
            self.i = 0;
            self.j += 1;
            if self.j >= self.grid.y_coords.len() {
                return None;
            }
        }
        let res = Some((self.grid.x_coords[self.i], self.grid.y_coords[self.j]));
        self.i += 1;
        res
    }
}

fn main() {
    let grid = Grid { x_coords: vec![3, 5, 7, 9], y_coords: vec![10, 20, 30, 40] };
    for (x, y) in grid {
        println!("point = {x}, {y}");
    }
}
```

Каждая реализация `IntoIterator` должна определять 2 типа:

- `Item` - перебираемый тип, такой как `i8`
- `IntoIter` - тип `Iterator`, возвращаемый методом `into_iter`

Обратите внимание, что `IntoIter` и `Iter` связаны: итератор должен иметь такой же тип `Item`. Это означает, что он должен возвращать `Option<Type>`.

В примере перебираются все комбинации координат `x` и `y`.

Обратите внимание, что `IntoIterator::into_iter` принимает владение (ownership) над `self`. Попробуйте дважды перебрать `grid` в функции `main`.

Решите эту проблему путем реализации `IntoIterator` для `&Grid` и сохранения ссылки на `Grid` в `GridIter`.

Аналогичная проблема может возникнуть при использовании стандартных типов: `for e in some_vec` принимает владение над `some_vec` и перебирает собственные элементы вектора. Для перебора ссылок на элементы вектора следует использовать `for e in &some_vec`.

__FromIterator__

Трейт [FromIterator](https://doc.rust-lang.org/std/iter/trait.FromIterator.html) позволяет создавать коллекции из `Iterator`:

```rust
fn main() {
    let primes = vec![2, 3, 5, 7];
    let prime_squares = primes.into_iter().map(|p| p * p).collect::<Vec<_>>();
    println!("prime_squares: {prime_squares:?}");
}
```

`Iterator` реализует

```rust
fn collect<B>(self) -> B
where
    B: FromIterator<Self::Item>,
    Self: Sized
```

Существует 2 способа определить `B` для этого метода:

- с помощью turbofish: `some_iterator.collect::<COLLECTION_TYPE>()`, как показано в примере. Сокращение `_` позволяет `Rust` вывести тип элементов вектора самостоятельно
- с помощью вывода типов: `let prime_squares: Vec<_> = some_iterator.collect()`

Базовые реализации `IntoIterator` существуют для `Vec`, `HashMap` и некоторых других типов. Существуют также более специализированные реализации, позволяющие делать клевые вещи, вроде преобразования `Iterator<Item = Result<V, E>>` в `Result<Vec<V>, E>`

__Упражнение: цепочка методов итератора__

В этом упражнении вам нужно найти и использовать некоторые методы трейта [Iterator](https://doc.rust-lang.org/std/iter/trait.Iterator.html) для реализации сложных вычислений.

Используйте выражение итератора и соберите (`collect`) результат для построения возвращаемого значения.

```rust
// Функция для вычисления разницы между элементами `values`, смещенными на `offset`.
// `values` перебираются по кругу.
//
// Элемент `n` результата - `values[(n+offset)%len] - values[n]`.
fn offset_differences<N>(offset: usize, values: Vec<N>) -> Vec<N>
where
    N: Copy + std::ops::Sub<Output = N>,
{
    todo!("реализуй меня")
}

fn main() {
    let res = offset_differences(1, vec![1, 3, 5, 7]);
    println!("{:?}", res);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_offset_one() {
        assert_eq!(offset_differences(1, vec![1, 3, 5, 7]), vec![2, 2, 2, -6]);
        assert_eq!(offset_differences(1, vec![1, 3, 5]), vec![2, 2, -4]);
        assert_eq!(offset_differences(1, vec![1, 3]), vec![2, -2]);
    }

    #[test]
    fn test_larger_offsets() {
        assert_eq!(offset_differences(2, vec![1, 3, 5, 7]), vec![4, 4, -4, -4]);
        assert_eq!(offset_differences(3, vec![1, 3, 5, 7]), vec![6, -2, -2, -2]);
        assert_eq!(offset_differences(4, vec![1, 3, 5, 7]), vec![0, 0, 0, 0]);
        assert_eq!(offset_differences(5, vec![1, 3, 5, 7]), vec![2, 2, 2, -6]);
    }

    #[test]
    fn test_custom_type() {
        assert_eq!(
            offset_differences(1, vec![1.0, 11.0, 5.0, 0.0]),
            vec![10.0, -6.0, -5.0, 1.0]
        );
    }

    #[test]
    fn test_degenerate_cases() {
        assert_eq!(offset_differences(1, vec![0]), vec![0]);
        assert_eq!(offset_differences(1, vec![1]), vec![0]);
        let empty: Vec<i32> = vec![];
        assert_eq!(offset_differences(1, empty), vec![]);
    }
}
```

<details>
<summary>Решение:</summary>

```rust
fn offset_differences<N>(offset: usize, values: Vec<N>) -> Vec<N>
where
    N: Copy + std::ops::Sub<Output = N>,
{
    let a = (&values).into_iter();
    let b = (&values).into_iter().cycle().skip(offset);
    a.zip(b).map(|(a, b)| *b - *a).take(values.len()).collect()
}
```

</details>
