---
title: "Тестирование"
description: "Модульные тесты, интеграционные тесты, макросы assert!"
date: 2026-05-20T05:00:00Z
weight: 18
image: "/images/rust/18-testirovanie-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Модульные/юнит-тесты__

`Rust` и `Cargo` поставляются с фреймворком для тестирования:

- модульные (unit) тесты поддерживаются прямо в коде, который мы пишем
- интеграционные (integration) тесты поддерживаются через директорию `tests`

Тесты помечаются с помощью директивы `#[test]`. Юнит-тесты часто помещаются во вложенный модуль `tests`. Директива `#[cfg(test)]` сообщает компилятору, что содержащийся далее код следует компилировать только при запуске тестов:

```rust
fn first_word(text: &str) -> &str {
    match text.find(' ') {
        Some(idx) => &text[..idx],
        None => &text,
    }
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_empty() {
        assert_eq!(first_word(""), "");
    }

    #[test]
    fn test_single_word() {
        assert_eq!(first_word("Hello"), "Hello");
    }

    #[test]
    fn test_multiple_words() {
        assert_eq!(first_word("Hello World"), "Hello");
    }
}
```

- Модульные тесты позволяют тестировать приватный функционал
- атрибут `#[cfg(test)]` активируется только при выполнении `cargo test`

__Другие типы тестов__

_Интеграционные тесты_

Интеграционные тесты используются для тестирования библиотеки от лица клиента.

Создаем файл `.rs` в директории `tests/`:

```rust
// tests/my_library.rs
use my_library::init;

#[test]
fn test_init() {
    assert!(init().is_ok());
}
```

Эти тесты имеют доступ только к публичному API тестируемого крейта.

_Документационные тесты_

`Rust` имеет встроенную поддержку документационных тестов:

```rust
/// Сокращает строку до указанной длины.
///
/// ```
/// # use playground::shorten_string;
/// assert_eq!(shorten_string("Hello World", 5), "Hello");
/// assert_eq!(shorten_string("Hello World", 20), "Hello World");
/// ```
pub fn shorten_string(s: &str, length: usize) -> &str {
    &s[..std::cmp::min(length, s.len())]
}

```

- Блоки кода в комментариях `///` считаются валидным кодом `Rust` (разумеется, если код компилируется)
- код будет скомпилирован и выполнен как часть `cargo test`
- добавление `#` в код скроет его из документации, но он по-прежнему будет компилироваться/выполняться

__Полезные крейты__

`Rust` предоставляет лишь базовую поддержку тестов.

Вот несколько крейтов, которые могут пригодиться для тестирования:

- [googletest](https://docs.rs/googletest) - комплексная библиотека тестирования в лучших традициях `GoogleTest` для `C++`
- [proptest](https://docs.rs/proptest) - библиотека тестирования на основе свойств (properties)
- [rstest](https://docs.rs/rstest) - библиотека тестирования, поддерживающая фикстуры (fixtures) и параметризованные тесты

__GoogleTest__

Крейт [googletest](https://docs.rs/googletest) позволяет создавать гибкие тесты с использованием сопоставителей (matchers):

```rust
use googletest::prelude::*;

#[googletest::test]
fn test_elements_are() {
    let value = vec!["foo", "bar", "baz"];
    expect_that!(value, elements_are!(eq("foo"), lt("xyz"), starts_with("b")));
}
```

Если мы изменим `b` на  `!` в последнем элементе, тест провалится с выдачей структурированного сообщения об ошибке:

```
---- test_elements_are stdout ----
Value of: value
Expected: has elements:
  0. is equal to "foo"
  1. is less than "xyz"
  2. starts with prefix "!"
Actual: ["foo", "bar", "baz"],
  where element #2 is "baz", which does not start with "!"
  at src/testing/googletest.rs:6:5
Error: See failure output above
```

Ремарки:

- выполните `cargo add googletest` для установки `googletest`
- `use googletest::prelude::*;` импортирует некоторые [часто используемые макросы и типы](https://docs.rs/googletest/latest/googletest/prelude/index.html)
- `googletest` предоставляет большое количество сопоставителей
- приятной особенностью `googletest` является то, что несоответствия в многострочных строках отображаются в виде разницы:

```rust
#[test]
fn test_multiline_string_diff() {
    let haiku = "Memory safety found,\n\
                 Rust's strong typing guides the way,\n\
                 Secure code you'll write.";
    assert_that!(
        haiku,
        eq("Memory safety found,\n\
            Rust's silly humor guides the way,\n\
            Secure code you'll write.")
    );
}
```

Вывод будет цветным:

```rust
    Value of: haiku
Expected: is equal to "Memory safety found,\nRust's silly humor guides the way,\nSecure code you'll write."
Actual: "Memory safety found,\nRust's strong typing guides the way,\nSecure code you'll write.",
  which isn't equal to "Memory safety found,\nRust's silly humor guides the way,\nSecure code you'll write."
Difference(-actual / +expected):
 Memory safety found,
-Rust's strong typing guides the way,
+Rust's silly humor guides the way,
 Secure code you'll write.
  at src/testing/googletest.rs:17:5=
```

__Мокинг__

Для мокинга (mocking - создание макета) широко используется библиотека [mockall](https://docs.rs/mockall/):

```rust
use std::time::Duration;

#[mockall::automock]
pub trait Pet {
    fn is_hungry(&self, since_last_meal: Duration) -> bool;
}

#[test]
fn test_robot_dog() {
    let mut mock_dog = MockPet::new();
    mock_dog.expect_is_hungry().return_const(true);
    assert_eq!(mock_dog.is_hungry(Duration::from_secs(10)), true);
}
```

Ремарки:

- для установки `mockall` выполните команду `cargo add mockall`
- на [crates.io доступны и другие библиотеки для мокинга](https://crates.io/keywords/mock), в частности, для мокинга HTTP-сервисов. Другие библиотеки работают аналогично `Mockall`: они позволяют легко получить макет реализации определенного трейта
- обратите внимание, что использование макетов несколько противоречиво: макеты позволяют полностью изолировать тест от его зависимостей. Непосредственным результатом является более быстрое и стабильное выполнение тестов. С другой стороны, макеты могут быть настроены неправильно и возвращать данные, отличные от того, что делали бы реальные зависимости. По-возможности следует использовать реальные зависимости. Например, многие базы данных позволяют настроить серверную часть в памяти (in-memory backend). Это означает, что мы получаем правильное поведение тестов, плюс они работают быстро и автоматически очищаются. Многие веб-фреймворки позволяют запускать внутрипроцессный сервер, который привязывается к произвольному порту на локальном хосте. Этот подход является более предпочтительным, чем мокинг, поскольку позволяет тестировать код в реальной среде
- `Mockall` предоставляет много полезных функций. В частности, мы можем настроить ожидания (expectations), которые зависят от переданных аргументов. Здесь мы используем это, чтобы создать макет кошки, которая проголодалась через 3 часа после того, как ее в последний раз покормили:

```rust
#[test]
fn test_robot_cat() {
    let mut mock_cat = MockPet::new();
    mock_cat
        .expect_is_hungry()
        .with(mockall::predicate::gt(Duration::from_secs(3 * 3600)))
        .return_const(true);
    mock_cat.expect_is_hungry().return_const(false);
    assert_eq!(mock_cat.is_hungry(Duration::from_secs(1 * 3600)), false);
    assert_eq!(mock_cat.is_hungry(Duration::from_secs(5 * 3600)), true);
}
```

- мы можем использовать `.times(n)`, чтобы ограничить количество вызовов фиктивного метода до `n` - при превышении этого лимита программа запаникует

__Линтер и Clippy__

Компилятор `Rust` выдает фантастические сообщения об ошибках, а также полезные подсказки (lints). [Clippy](https://doc.rust-lang.org/clippy/) предоставляет еще больше подсказок, организованных в группы, которые можно включать/выключать для каждого проекта.

```rust
#[deny(clippy::cast_possible_truncation)]
fn main() {
    let x = 3;
    while (x < 70000) {
        x *= 2;
    }
    println!("X помещается в u16, верно? {}", x as u16);
}
```

__Упражнение: алгоритм Луна__

[Алгоритм Луна](https://en.wikipedia.org/wiki/Luhn_algorithm) используется для проверки номеров кредитных карт. Алгоритм принимает строку на вход и выполняет следующие действия:

- игнорируем все пробелы
- отклоняем номера, содержащие менее двух цифр
- двигаясь справа налево, удваиваем каждую вторую цифру: для числа 1234 удваиваем 3 и 1, для числа 98765 удваиваем 6 и 8
- после удвоения цифры суммируем цифры, если результат больше 9. Таким образом, удвоение 7 дает 14, что дает 1 + 4 = 5
- суммируем все неудвоенные и удвоенные цифры
- номер кредитной карты действителен, если сумма заканчивается на 0

Приведенный код содержит ошибочную реализацию алгоритма Луна, а также два модульных теста, которые подтверждают, что большая часть алгоритма реализована правильно:

```rust
pub fn luhn(cc_number: &str) -> bool {
    let mut sum = 0;
    let mut double = false;

    for c in cc_number.chars().rev() {
        if let Some(digit) = c.to_digit(10) {
            if double {
                let double_digit = digit * 2;
                sum +=
                    if double_digit > 9 { double_digit - 9 } else { double_digit };
            } else {
                sum += digit;
            }
            double = !double;
        } else {
            continue;
        }
    }

    sum % 10 == 0
}

fn main() {
    let cc_number = "1234 5678 1234 5670";
    println!(
        "{cc_number} является действительным номером кредитной карты? {}",
        if luhn(cc_number) { "Да" } else { "Нет" }
    );
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_valid_cc_number() {
        assert!(luhn("4263 9826 4026 9299"));
        assert!(luhn("4539 3195 0343 6467"));
        assert!(luhn("7992 7398 713"));
    }

    #[test]
    fn test_invalid_cc_number() {
        assert!(!luhn("4223 9826 4026 9299"));
        assert!(!luhn("4539 3195 0343 6476"));
        assert!(!luhn("8273 1232 7352 0569"));
    }

    #[test]
    fn test_non_digit_cc_number() {
        assert!(!luhn("foo"));
        assert!(!luhn("foo 0 0"));
    }

    #[test]
    fn test_empty_cc_number() {
        assert!(!luhn(""));
        assert!(!luhn(" "));
        assert!(!luhn("  "));
        assert!(!luhn("    "));
    }

    #[test]
    fn test_single_digit_cc_number() {
        assert!(!luhn("0"));
    }

    #[test]
    fn test_two_digit_cc_number() {
        assert!(luhn(" 0 0 "));
    }
}
```

<details>
<summary>Решение:</summary>

```rust
pub fn luhn(cc_number: &str) -> bool {
    // Итоговая сумма цифр
    let mut sum = 0;
    // Индикатор необходимости удвоения цифры
    let mut double = false;
    // Количество цифр
    let mut digits = 0;

    // Перебираем цифры справа налево
    for c in cc_number.chars().rev() {
        // Если символ является валидным десятичным числом
        if let Some(digit) = c.to_digit(10) {
            // Увеличиваем количество цифр
            digits += 1;
            // Если цифру нужно удвоить
            if double {
                let double_digit = digit * 2;
                // Если удвоенная цифра больше 9, вычитаем из нее 9:
                // если получили 14, то 1 + 4 = 5, что эквивалентно 14 - 9 = 5
                sum +=
                    if double_digit > 9 { double_digit - 9 } else { double_digit };
            // Иначе просто добавляем цифру к сумме
            } else {
                sum += digit;
            }
            // Удваиваем каждую вторую цифру
            double = !double;
        // Игнорируем пробелы
        } else if c.is_whitespace() {
            continue;
        // Если строка содержит символ, отличающийся от цифры и пробела
        } else {
            return false;
        }
    }

    // Цифр должно быть больше двух и сумма должна заканчиваться на 0
    digits >= 2 && sum % 10 == 0
}
```

</details>
