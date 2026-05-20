---
title: "Сопоставление с образцом"
description: "match, деструктуризация, охранные выражения, if let и while let"
date: 2026-05-20T05:00:00Z
weight: 7
image: "/images/rust/07-sopostavlenie-s-obrazcom-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Деструктуризация__

Как и кортежи (tuples), структуры (structs) и перечисления (enums) также могут деструктурироваться (destructure) сопоставлением:

_Структуры_

```rust
struct Foo {
    x: (u32, u32),
    y: u32,
}

// Запрещаем форматирование
#[rustfmt::skip]
fn main() {
    let foo = Foo { x: (1, 2), y: 3 };
    match foo {
        Foo { x: (1, b), y } => println!("x.0 = 1, b = {b}, y = {y}"),
        Foo { y: 2, x: i }   => println!("y = 2, x = {i:?}"),
        Foo { y, .. }        => println!("y = {y}, другие поля игнорируются"),
    }
}
```

_Перечисления_

Шаблоны (patterns) могут использоваться для привязки переменных к частям значений. Это, помимо прочего, позволяет исследовать структуру типов. Начнем с определения простого `enum`:

```rust
enum Result {
    Ok(i32),
    Err(String),
}

fn divide_in_two(n: i32) -> Result {
    if n % 2 == 0 {
        Result::Ok(n / 2)
    } else {
        Result::Err(format!("нельзя разделить {n} на 2 равные части"))
    }
}

fn main() {
    let n = 100;
    match divide_in_two(n) {
        Result::Ok(half) => println!("{n}, деленное на 2: {half}"),
        Result::Err(msg) => println!("возникла ошибка: {msg}"),
    }
}
```

Здесь для деструктуризации `Result` используется 2 блока (руки/рукава - arms). В первом блоке `half` привязывается к значению внутри варианта `Ok`. Во втором блоке `msg` привязывается к сообщению об ошибке (внутри варианта `Err`).

Структуры:

- измените литеральные значения в `foo` для совпадения с другими шаблонами
- добавьте новое поле в `Foo` и модифицируйте шаблон соответствующим образом

Перечисления:

- выражение `if-else` возвращает перечисление, которое распаковывается с помощью `match`
- добавьте третий вариант в перечисление и изучите сообщение об ошибке
- доступ к значениям в вариантах перечисления возможен только после сопоставления с шаблоном
- изучите ошибки, связанные с тем, что сопоставление не является исчерпывающим

__Поток управления `let`__

`Rust` предоставляет несколько конструкций управления потоком выполнения программы, которых нет в других языках программирования и которые используются для сопоставления с шаблоном:

- `if let`
- `while let`
- `match`

_if let_

Выражение [if-let](https://doc.rust-lang.org/reference/expressions/if-expr.html#if-let-expressions) позволяет выполнять код в зависимости от совпадения значения с шаблоном:

```rust
fn sleep_for(secs: f32) {
    let dur = if let Ok(dur) = std::time::Duration::try_from_secs_f32(secs) {
        dur
    } else {
        std::time::Duration::from_millis(500)
    };
    std::thread::sleep(dur);
    println!("спал в течение {:?}", dur);
}

fn main() {
    // Выполнится код блока `else`
    sleep_for(-10.0);
    // Выполнится код блока `if`
    sleep_for(0.8);
}
```

_let-else_

Для обычного случая сопоставления с шаблоном и возврата из функции следует использовать [let-else](https://doc.rust-lang.org/rust-by-example/flow_control/let_else.html). Код блока `else` должен прерывать поток выполнения программы (`return`, `break`, `panic!` и т.п.).

```rust
fn hex_or_die_trying(maybe_string: Option<String>) -> Result<u32, String> {
    let s = if let Some(s) = maybe_string {
        s
    } else {
        return Err(String::from("получено `None`"));
    };

    let first_byte_char = if let Some(first_byte_char) = s.chars().next() {
        first_byte_char
    } else {
        return Err(String::from("получена пустая строка"));
    };

    if let Some(digit) = first_byte_char.to_digit(16) {
        Ok(digit)
    } else {
        Err(String::from("не шестнадцатеричное число"))
    }
}

fn main() {
    println!("результат: {:?}", hex_or_die_trying(Some(String::from("foo")))); // 15 - байтовое представление символа `f`
}
```

Выражение [while-let](https://doc.rust-lang.org/reference/expressions/loop-expr.html#predicate-pattern-loops) повторно проверяет соответствие значения шаблону:

```rust
fn main() {
    let mut name = String::from("Comprehensive Rust 🦀");
    while let Some(c) = name.pop() {
        println!("символ: {c}");
    }
    // Существуют более эффективные способы 😉
}
```

Здесь [String::pop()](https://doc.rust-lang.org/stable/std/string/struct.String.html#method.pop) возвращает `Some(c)` до тех пор, пока строка не окажется пустой, после чего возвращается `None`. `while-let` позволяет перебирать все элементы.

if-let:

- в отличие от `match`, `if-let` не должно охватывать все случаи. Поэтому его использование может быть менее многословным, чем использование `match`
- обычным способом использования `if-let` является обработка `Some` при работе с `Option`
- в отличие от `match`, `if-let` не поддерживает защитников сопоставления (match guards)

let-else:

- `let-else` поддерживает распаковку (flattening) вложенного кода. Перепишем пример следующим образом:

```rust
fn hex_or_die_trying(maybe_string: Option<String>) -> Result<u32, String> {
    let Some(s) = maybe_string else {
        return Err(String::from("получено `None`"));
    };

    let Some(first_byte_char) = s.chars().next() else {
        return Err(String::from("получена пустая строка"));
    };

    let Some(digit) = first_byte_char.to_digit(16) else {
        return Err(String::from("не шестнадцатеричное число"));
    };

    return Ok(digit);
}
```

while-let:

- цикл `while-let` повторяется, пока значение совпадает с шаблоном
- цикл `while-let` в примере можно сделать бесконечным с инструкцией `if` внутри, которая прерывает цикл, когда `name.pop()` ничего не возвращает

__Упражнение: оценка выражения__

Напишем простой рекурсивный вычислитель арифметических выражений.

Тип `Box` представляет собой умный указатель (smart pointer), который мы подробно рассмотрим позже. Выражение можно "упаковать" с помощью `Box::new()`, как показано в тестах. Для вычисления упакованного выражения, следует использовать оператор разыменования (`*`): `eval(*boxed_expr)`.

Некоторые выражения не могут быть вычислены и возвращают ошибку. Стандартный тип `Result<Value, String>` - это перечисление, которое представляет успешное значение (`Ok(Value)`) или ошибку (`Err(String)`). Мы подробно рассмотрим этот тип позже.

```rust
// Операция, выполняемая над двумя подвыражениями
#[derive(Debug)]
enum Operation {
    Add,
    Sub,
    Mul,
    Div,
}

// Выражение в форме дерева
#[derive(Debug)]
enum Expression {
    // Операция над двумя подвыражениями
    Op {
        op: Operation,
        left: Box<Expression>,
        right: Box<Expression>,
    },

    // Литеральное значение
    Value(i64),
}

// Рекурсивный вычислитель арифметических выражений
fn eval(e: Expression) -> Result<i64, String> {
    todo!("реализуй меня")
}

fn main() {
    let expr = Expression::Op {
        op: Operation::Sub,
        left: Box::new(Expression::Value(20)),
        right: Box::new(Expression::Value(10)),
    };
    println!("выражение: {:?}", expr);
    println!("результат: {:?}", eval(expr));
}

// Модуль с тестами - код компилируется только при запуске тестов с помощью команды `cargo test`
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_value() {
        assert_eq!(eval(Expression::Value(19)), Ok(19));
    }

    #[test]
    fn test_sum() {
        assert_eq!(
            eval(Expression::Op {
                op: Operation::Add,
                left: Box::new(Expression::Value(10)),
                right: Box::new(Expression::Value(20)),
            }),
            Ok(30)
        );
    }

    #[test]
    fn test_recursion() {
        let term1 = Expression::Op {
            op: Operation::Mul,
            left: Box::new(Expression::Value(10)),
            right: Box::new(Expression::Value(9)),
        };
        let term2 = Expression::Op {
            op: Operation::Mul,
            left: Box::new(Expression::Op {
                op: Operation::Sub,
                left: Box::new(Expression::Value(3)),
                right: Box::new(Expression::Value(4)),
            }),
            right: Box::new(Expression::Value(5)),
        };
        assert_eq!(
            eval(Expression::Op {
                op: Operation::Add,
                left: Box::new(term1),
                right: Box::new(term2),
            }),
            Ok(85)
        );
    }

    #[test]
    fn test_error() {
        assert_eq!(
            eval(Expression::Op {
                op: Operation::Div,
                left: Box::new(Expression::Value(99)),
                right: Box::new(Expression::Value(0)),
            }),
            Err(String::from("деление на ноль"))
        );
    }
}
```

<details>
<summary>Решение:</summary>

```rust
fn eval(e: Expression) -> Result<i64, String> {
    // Определяем вариант
    match e {
        // Операция.
        // Деструктуризация
        Expression::Op { op, left, right } => {
            // Рекурсивно вычисляем левое подвыражение
            let left = match eval(*left) {
                Ok(v) => v,
                Err(e) => return e,
            };
            // Рекурсивно вычисляем правое подвыражение
            let right = match eval(*right) {
                Ok(v) => v,
                Err(e) => return e,
            };
            // Возвращаем результат, упакованный в `Ok`
            Ok(
              // Определяем тип операции
              match op {
                  Operation::Add => left + right,
                  Operation::Sub => left - right,
                  Operation::Mul => left * right,
                  Operation::Div => {
                      // Если правый операнд равняется 0
                      if right == 0 {
                          // Возвращаем вызывающему (caller) сообщение об ошибке, обернутое в `Err`.
                          // Мы распространяем (propagate) ошибку, поэтому она не оборачивается в `Ok`
                          return Err(String::from("деление на ноль"));
                      } else {
                          left / right
                      }
                  }
              }
            )
        }
        // Значение.
        // Просто возвращаем значение, упакованное в `Ok`
        Expression::Value(v) => Ok(v),
    }
}
```

</details>
