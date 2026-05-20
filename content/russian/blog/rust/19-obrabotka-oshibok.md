---
title: "Обработка ошибок"
description: "Result, Error, thiserror, anyhow, проброс ошибок"
date: 2026-05-20T05:00:00Z
weight: 19
image: "/images/rust/19-obrabotka-oshibok-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Паника__

Фатальные ошибки обрабатываются в `Rust` с помощью "паники" (panic).

Паника происходит при возникновении фатальной ошибки во время выполнения:

```rust
fn main() {
    let v = vec![10, 20, 30];
    println!("v[100]: {}", v[100]);
}
```

Ремарки:

- паника связана с неисправимыми и неожиданными ошибками:
  - паника - это симптомы ошибок в программе
  - сбои во время выполнения, такие как неудачная проверка границ (boundaries), могут вызвать панику
  - утверждения (например, `assert!`) паникуют при неудаче
  - для целенаправленной паники можно использовать макрос `panic!`
- паника "разматывает" (unwind) стек, сбрасывая значения так же, как если бы функции вернули значения
- в примере для безопасного доступа к элементу вектора по индексу можно использовать `Vec::get`

По умолчанию паника разматывает стек. Разматывание может быть перехвачено:

```rust
use std::panic;

fn main() {
    let result = panic::catch_unwind(|| "No problem here!");
    println!("{result:?}");

    let result = panic::catch_unwind(|| {
        panic!("Oh no!");
    });
    println!("{result:?}");
}
```

- Не пытайтесь реализовать исключения с помощью `catch_unwind`
- это может быть полезно на серверах, которые должны продолжать работать даже в случае сбоя одного запроса
- это не работает при установке `panic = 'abort'` в `Cargo.toml`

__Оператор ?__

Ошибки времени выполнения, такие как отказ в соединении или отсутствие файла, обрабатываются с помощью типа `Result`, но сопоставление (matching) этого типа при каждом вызове может быть утомительным и излишним. Оператор `?` используется для возврата ошибок вызывающему (caller). Он позволяет заменить

```rust
match some_expression {
    Ok(value) => value,
    Err(err) => return Err(err),
}
```

на

```rust
some_expression?
```

Попробуйте упростить обработку ошибок в следующем коде:

```rust
use std::io::Read;
use std::{fs, io};

fn read_username(path: &str) -> Result<String, io::Error> {
    let username_file_result = fs::File::open(path);
    let mut username_file = match username_file_result {
        Ok(file) => file,
        Err(err) => return Err(err),
    };

    let mut username = String::new();
    match username_file.read_to_string(&mut username) {
        Ok(_) => Ok(username),
        Err(err) => Err(err),
    }
}

fn main() {
    // fs::write("config.dat", "alice").unwrap();
    let username = read_username("config.dat");
    println!("username or error: {username:?}");
}
```

Подсказки:

- переменная `username` может быть либо `Ok(String)`, либо `Err(error)`
- используйте `fs::write` для тестирования разных случаев: отсутствие файла, пустой файл, файл с именем пользователя
- обратите внимание, что `main` может возвращать `Result<(), E>` до тех пор, пока реализует `std::process:Termination`. На практике это означает, что `E` реализует `Debug`. Исполняемый файл напечатает вариант `Err` и вернет ненулевой статус выхода в случае ошибки

__Преобразования Try__

Оператор `?` работает немного сложнее, чем можно подумать.

Это:

```rust
expression?
```

Эквивалентно этому:

```rust
match expression {
    Ok(value) => value,
    Err(err)  => return Err(From::from(err)),
}
```

Вызов `From::from` здесь означает, что мы пытаемся преобразовать тип ошибки в тип, возвращаемый функцией. Это позволяет легко преобразовать локальные ошибки в ошибки более высокого уровня.

_Пример_

```rust
use std::error::Error;
use std::fmt::{self, Display, Formatter};
use std::fs::File;
use std::io::{self, Read};

#[derive(Debug)]
enum ReadUsernameError {
    IoError(io::Error),
    EmptyUsername(String),
}

impl Error for ReadUsernameError {}

impl Display for ReadUsernameError {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        match self {
            Self::IoError(e) => write!(f, "Ошибка ввода/вывода: {e}"),
            Self::EmptyUsername(path) => write!(f, "Имя пользователя отсутствует в {path}"),
        }
    }
}

impl From<io::Error> for ReadUsernameError {
    fn from(err: io::Error) -> Self {
        Self::IoError(err)
    }
}

fn read_username(path: &str) -> Result<String, ReadUsernameError> {
    let mut username = String::with_capacity(100);
    File::open(path)?.read_to_string(&mut username)?;
    if username.is_empty() {
        return Err(ReadUsernameError::EmptyUsername(String::from(path)));
    }
    Ok(username)
}

fn main() {
    // fs::write("config.dat", "").unwrap();
    let username = read_username("config.dat");
    println!("Имя пользователя или ошибка: {username:?}");
}
```

Оператор `?` должен возвращать значение, совместимое с типом значения, возвращаемого функцией. Для `Result` это означает, что типы ошибок должны быть совместимыми. Функция, возвращающая `Result<T, ErrorOuter>`, может использовать `?` только для значения типа `Result<U, ErrorInner>`, если `ErrorOuter` и `ErrorInner` имеют один и тот же тип, или если `ErrorOuter` реализует `From<ErrorInner>`.

Распространенной альтернативой реализации `From` является `Result::map_err`, особенно когда преобразование происходит только в одном месте.

Для `Option` нет требований совместимости. Функция, возвращающая `Option<T>`, может использовать оператор `?` на `Option<U>` для произвольных типов `T` и `U`.

Функция, возвращающая `Result`, не может использовать `?` на `Option`, и наоборот. Однако, `Option::ok_or` преобразует `Option` в `Result`, а `Result::ok` - `Result` в `Option`.

__Динамические типы ошибок__

Иногда мы хотим возвращать любой тип ошибки без создания перечисления, охватывающего все варианты. Трейт `std::error::Error` позволяет легко создать трейт-объект, который может содержать любую ошибку:

```rust
use std::error::Error;
use std::fs;
use std::io::Read;

fn read_count(path: &str) -> Result<i32, Box<dyn Error>> {
    let mut count_str = String::new();
    fs::File::open(path)?.read_to_string(&mut count_str)?;
    let count: i32 = count_str.parse()?;
    Ok(count)
}

fn main() {
    fs::write("count.dat", "1i3").unwrap();
    match read_count("count.dat") {
        Ok(count) => println!("Содержимое: {count}"),
        Err(err) => println!("Ошибка: {err}"),
    }
}
```

Функция `read_count` может возвращать `std::io::Error` (из операций с файлом) или `std::num::ParseIntError` (из `String::parse`).

Использование динамических (boxing) ошибок сокращает количество кода, но лишает возможности по-разному обрабатывать разные ошибки. Поэтому использовать `Box<dyn Error>` в общедоступном API библиотеки не рекомендуется, но это может быть хорошим вариантом, когда мы просто хотим где-то отображать сообщение об ошибке.

При создании кастомных типов ошибок убедитесь, что они реализуют `std::error::Error`, чтобы их можно было оборачивать в `Box`.

__thiserror и anyhow__

Крейты [thiserror](https://docs.rs/thiserror/) и [anyhow](https://docs.rs/anyhow/) широко используются для упрощения обработки ошибок. `thiserror` помогает создавать кастомные типы ошибок, реализующие `From<T>`. `anyhow` помогает с обработкой ошибок в функциях, включая добавление контекстуальной информации в ошибки.

```rust
use anyhow::{bail, Context, Result};
use std::fs;
use std::io::Read;
use thiserror::Error;

#[derive(Clone, Debug, Eq, Error, PartialEq)]
#[error("Имя пользователя отсутствует в {0}")]
struct EmptyUsernameError(String);

fn read_username(path: &str) -> Result<String> {
    let mut username = String::with_capacity(100);
    fs::File::open(path)
        .with_context(|| format!("Ошибка при открытии {path}"))?
        .read_to_string(&mut username)
        .context("Ошибка при чтении")?;
    if username.is_empty() {
        bail!(EmptyUsernameError(path.to_string()));
    }
    Ok(username)
}

fn main() {
    // fs::write("config.dat", "").unwrap();
    match read_username("config.dat") {
        Ok(username) => println!("Имя пользователя: {username}"),
        Err(err) => println!("Ошибка: {err:?}"),
    }
}
```

`thiserror`:

- макрос `error` предоставляется `thiserror` и содержит большое количество атрибутов для лаконичного определения типов ошибок
- трейт `std::error::Error` реализуется автоматически
- сообщение из `#[error]` используется для автоматической реализации трейта `Display`

`anyhow`:

- `anyhow::Error` - это обертка над `Box<dyn Error>`. Опять же это не лучший выбор для общедоступного API библиотеки, но он широко используется в приложениях
- `anyhow::Result<V>` - это синоним типа `Result<V, anyhow::Error>`
- при необходимости фактический тип ошибки внутри него можно извлечь для проверки
- `anyhow::Context` - это трейт, реализованный для стандартных типов `Result` и `Option`. `use anyhow::Context` необходим для включения `.context()` и `.with_context()` на этих типах

__Упражнение: без паники__

Следующий код реализует очень простой синтаксический анализатор языка выражений. Однако он обрабатывает ошибки путем паники. Перепишите его, чтобы вместо этого использовать идиоматическую обработку ошибок и распространять ошибки на возврат из `main`. Не стесняйтесь использовать `thiserror` и `anyhow`.

Подсказка: начните исправлять ошибки в функции `parse`. После того, как она заработает, обновите `Tokenizer` для реализации `Iterator<Item=Result<Token, TokenizerError>>` и обработайте его в парсере.

```rust
use std::iter::Peekable;
use std::str::Chars;

// Арифметический оператор
#[derive(Debug, PartialEq, Clone, Copy)]
enum Op {
    Add,
    Sub,
}

// Токен языка
#[derive(Debug, PartialEq)]
enum Token {
    Number(String),
    Identifier(String),
    Operator(Op),
}

// Выражение языка
#[derive(Debug, PartialEq)]
enum Expression {
    // Ссылка на переменную
    Var(String),
    // Литеральное число
    Number(u32),
    // Бинарная операция
    Operation(Box<Expression>, Op, Box<Expression>),
}

fn tokenize(input: &str) -> Tokenizer {
    return Tokenizer(input.chars().peekable());
}

struct Tokenizer<'a>(Peekable<Chars<'a>>);

impl<'a> Iterator for Tokenizer<'a> {
    type Item = Token;

    fn next(&mut self) -> Option<Token> {
        let c = self.0.next()?;
        match c {
            '0'..='9' => {
                let mut num = String::from(c);
                while let Some(c @ '0'..='9') = self.0.peek() {
                    num.push(*c);
                    self.0.next();
                }
                Some(Token::Number(num))
            }
            'a'..='z' => {
                let mut ident = String::from(c);
                while let Some(c @ ('a'..='z' | '_' | '0'..='9')) = self.0.peek() {
                    ident.push(*c);
                    self.0.next();
                }
                Some(Token::Identifier(ident))
            }
            '+' => Some(Token::Operator(Op::Add)),
            '-' => Some(Token::Operator(Op::Sub)),
            _ => panic!("Неожиданный символ {c}"),
        }
    }
}

fn parse(input: &str) -> Expression {
    let mut tokens = tokenize(input);

    fn parse_expr<'a>(tokens: &mut Tokenizer<'a>) -> Expression {
        let Some(tok) = tokens.next() else {
            panic!("Неожиданный конец ввода");
        };
        let expr = match tok {
            Token::Number(num) => {
                let v = num.parse().expect("Невалидное 32-битное целое число");
                Expression::Number(v)
            }
            Token::Identifier(ident) => Expression::Var(ident),
            Token::Operator(_) => panic!("Неожиданный токен {tok:?}"),
        };
        // Проверяем наличие бинарной операции
        match tokens.next() {
            None => expr,
            Some(Token::Operator(op)) => Expression::Operation(
                Box::new(expr),
                op,
                Box::new(parse_expr(tokens)),
            ),
            Some(tok) => panic!("Неожиданный токен {tok:?}"),
        }
    }

    parse_expr(&mut tokens)
}

fn main() {
    let expr = parse("10+foo+20-30");
    println!("{expr:?}");
}
```

<details>
<summary>Решение:</summary>

```rust
use thiserror::Error;
use std::iter::Peekable;
use std::str::Chars;

#[derive(Debug, PartialEq, Clone, Copy)]
enum Op {
    Add,
    Sub,
}

#[derive(Debug, PartialEq)]
enum Token {
    Number(String),
    Identifier(String),
    Operator(Op),
}

#[derive(Debug, PartialEq)]
enum Expression {
    Var(String),
    Number(u32),
    Operation(Box<Expression>, Op, Box<Expression>),
}

fn tokenize(input: &str) -> Tokenizer {
    return Tokenizer(input.chars().peekable());
}

#[derive(Debug, Error)]
enum TokenizerError {
    #[error("Неожиданный символ {0}")]
    UnexpectedCharacter(char),
}

struct Tokenizer<'a>(Peekable<Chars<'a>>);

impl<'a> Iterator for Tokenizer<'a> {
    type Item = Result<Token, TokenizerError>;

    fn next(&mut self) -> Option<Result<Token, TokenizerError>> {
        let c = self.0.next()?;
        match c {
            '0'..='9' => {
                let mut num = String::from(c);
                while let Some(c @ '0'..='9') = self.0.peek() {
                    num.push(*c);
                    self.0.next();
                }
                Some(Ok(Token::Number(num)))
            }
            'a'..='z' => {
                let mut ident = String::from(c);
                while let Some(c @ ('a'..='z' | '_' | '0'..='9')) = self.0.peek() {
                    ident.push(*c);
                    self.0.next();
                }
                Some(Ok(Token::Identifier(ident)))
            }
            '+' => Some(Ok(Token::Operator(Op::Add))),
            '-' => Some(Ok(Token::Operator(Op::Sub))),
            _ => Some(Err(TokenizerError::UnexpectedCharacter(c))),
        }
    }
}

#[derive(Debug, Error)]
enum ParserError {
    #[error("Ошибка токенизатора: {0}")]
    TokenizerError(#[from] TokenizerError),
    #[error("Неожиданный конец ввода")]
    UnexpectedEOF,
    #[error("Неожиданный токен {0:?}")]
    UnexpectedToken(Token),
    #[error("Невалидное число")]
    InvalidNumber(#[from] std::num::ParseIntError),
}

fn parse(input: &str) -> Result<Expression, ParserError> {
    let mut tokens = tokenize(input);

    fn parse_expr<'a>(
        tokens: &mut Tokenizer<'a>,
    ) -> Result<Expression, ParserError> {
        let tok = tokens.next().ok_or(ParserError::UnexpectedEOF)??;
        let expr = match tok {
            Token::Number(num) => {
                let v = num.parse()?;
                Expression::Number(v)
            }
            Token::Identifier(ident) => Expression::Var(ident),
            Token::Operator(_) => return Err(ParserError::UnexpectedToken(tok)),
        };

        Ok(match tokens.next() {
            None => expr,
            Some(Ok(Token::Operator(op))) => Expression::Operation(
                Box::new(expr),
                op,
                Box::new(parse_expr(tokens)?),
            ),
            Some(Err(e)) => return Err(e.into()),
            Some(Ok(tok)) => return Err(ParserError::UnexpectedToken(tok)),
        })
    }

    parse_expr(&mut tokens)
}

fn main() -> anyhow::Result<()> {
    let expr = parse("10+foo+20-30")?;
    println!("{expr:?}");
    Ok(())
}
```

</details>
