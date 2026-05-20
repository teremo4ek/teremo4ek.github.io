---
title: "Срезы и времена жизни"
description: "Срезы строк и массивов, аннотации времён жизни, elision"
date: 2026-05-20T05:00:00Z
weight: 15
image: "/images/rust/15-srezy-i-vremena-zhizni-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Срезы__

Срез (slice) - это представление (view) (часть) большой коллекции значений:

```rust
fn main() {
    let mut a: [i32; 6] = [10, 20, 30, 40, 50, 60];
    println!("a: {a:?}");

    let s: &[i32] = &a[2..4];

    println!("s: {s:?}");
}
```

- Срезы заимствуют данные из исходного типа
- Вопрос: что произойдет, если модифицировать `a[3]` перед выводом `s` в терминал?

Ремарки:

- мы создаем срез путем заимствования `a` и определения начального и конечного индексов в квадратных скобках
- если срез начинается с индекса `0`, синтаксис диапазона `Rust` позволяет не указывать начальный индекс: `&a[0..a.len()]` == `&a[..a.len()]`
- тоже справедливо для конечного индекса: `&a[2..a.len()]` == `&a[2..]`
- срез всего массива можно создать с помощью `&a[..]`
- `s` - это ссылка на срез целых чисел со знаком. Обратите внимание, что в типе `s` (`&[i32]`) не упоминается длина массива. Это позволяет вычислять срезы разных размеров
- срезы всегда заимствуют значения объектов. В примере `a` остается "живой" (в области видимости) до тех пор, пока "жив" его срез
- вопрос об изменении `a[3]` может вызвать интересную дискуссию, но ответ заключается в том, что из соображений безопасности памяти мы не можем сделать это через `a` на данном этапе выполнения кода, но мы можем безопасно читать данные как из `a`, так и из `s`. Это работает до создания среза и после вызова `println!`, когда срез больше не используется

__Строки__

Теперь мы можем разобраться с типом `&str`: это почти `&[char]`, но с данными, хранящимися в кодировке переменной длины (UTF-8).

```rust
fn main() {
    let s1: &str = "World";
    println!("s1: {s1}");

    let mut s2: String = String::from("Hello ");
    println!("s2: {s2}");
    s2.push_str(s1);
    println!("s2: {s2}");

    let s3: &str = &s2[6..];
    println!("s3: {s3}");
}
```

- `&str` - иммутабельная ссылка на строковый срез
- `String` - мутабельная ссылка на буфер

Ремарки:

- `&str` - это срез строки, иммутабельная ссылка на закодированные в UTF-8 текстовые данные, хранящиеся в блоке памяти. Строковые литералы (`"Hello"`) хранятся в бинарнике (исполняемом файле) программы
- тип `String` - это обертка над вектором байтов. Как и `Vec<T>`, он является собственным (owned)
- `String::from()` создает строку из литерала строки; `String::new()` создает новую пустую строку, в которую можно добавлять строковые данные с помощью методов `push` и `push_str`
- макрос `format!` генерирует собственную строку из динамических значений. Стиль его форматирования схож с `println!`
- мы можем заимствовать срезы `&str` из `String` через `&` и опциональный диапазон выбора (range selection). Если выбран диапазон байтов, который не совпадает с границами символов (character boundaries), выражение запаникует. Итератор `chars` перебирает символы и является предпочтительным способом правильного извлечения символов
- байтовые строки позволяют создавать `&[u8]` напрямую:

```rust
fn main() {
    let byte_string = b"abc";
    println!("{:?}", byte_string);
    assert_eq!(byte_string, &[97, 98, 99])
}
```

__Аннотации времен жизни__

Ссылка имеет время жизни (lifetime), она не должна "переживать" значение, на которое ссылается. Соблюдение этого правила обеспечивается контроллером заимствований (borrow checker).

Время жизни может определяться неявно - то, что мы видели до сих пор. Времена жизни также могут быть явными: `&'a Point`, `&'static str`. Времена жизни начинаются с `'` и `'a` - имя по умолчанию. `&'a Point` читается как "заимствование структуры `Point`, которое является валидным на протяжении времени жизни `a`".

Времена жизни всегда выводятся (inferred) компилятором, они не могут присваиваться явно. Явные аннотации (annotations) времен жизни создают ограничения в случае неопределенности; компилятор предоставляет валидное решение в рамках этих ограничений.

Времена жизни становятся сложными, когда значения передаются в и возвращаются из функции:

```rust
#[derive(Debug)]
struct Point(i32, i32);

fn left_most(p1: &Point, p2: &Point) -> &Point {
    if p1.0 < p2.0 {
        p1
    } else {
        p2
    }
}

fn main() {
    let p1: Point = Point(10, 10);
    let p2: Point = Point(20, 20);
    let p3 = left_most(&p1, &p2); // каково время жизни `p3`?
    println!("p3: {p3:?}");
}
```

В примере компилятор не может самостоятельно определить время жизни `p3`. Ему требуется наша помощь:

```rust
fn left_most<'a>(p1: &'a Point, p2: &'a Point) -> &'a Point { .. }
```

Возвращаемое значение должно жить как минимум также долго, как передаваемые аргументы.

В обычных ситуациях явные аннотации времен жизни не требуются.

__Времена жизни в функциях__

Времена жизни параметров функции и возвращаемого функцией значения должны быть полностью определены, но в ряде случаев `Rust` позволяет опустить (elide) аннотации времен жизни. На этот счет существует [несколько простых правил](https://doc.rust-lang.org/nomicon/lifetime-elision.html):

- каждому аргументу присваивается аннотация времени жизни при отсутствии
- если функция принимает только один параметр, его время жизни становится временем жизни возвращаемого функцией значения
- если функция принимает несколько параметров, но первым параметром является `self`, время жизни `self` становится временем жизни возвращаемого функцией значения

```rust
#[derive(Debug)]
struct Point(i32, i32);

fn cab_distance(p1: &Point, p2: &Point) -> i32 {
    (p1.0 - p2.0).abs() + (p1.1 - p2.1).abs()
}

fn nearest<'a>(points: &'a [Point], query: &Point) -> Option<&'a Point> {
    let mut nearest = None;
    for p in points {
        if let Some((_, nearest_dist)) = nearest {
            let dist = cab_distance(p, query);
            if dist < nearest_dist {
                nearest = Some((p, dist));
            }
        } else {
            nearest = Some((p, cab_distance(p, query)));
        };
    }
    nearest.map(|(p, _)| p)
}

fn main() {
    println!(
        "{:?}",
        nearest(
            &[Point(1, 0), Point(1, 0), Point(-1, 0), Point(0, -1),],
            &Point(0, 2)
        )
    );
}
```

Функция `cab_distance` не требует явных аннотаций времен жизни, поскольку `p1` и `p2` имеют одинаковый тип.

Параметры функции `nearest` имеют разные типы, поэтому функция требует явных аннотаций времен жизни. Попробуйте переписать ее сигнатуру следующим образом:

```rust
fn nearest<'a, 'q'>(points: &'a [Point], query: &'q Point) -> Option<&'q Point> { .. }
```

Такой код не компилируется. Это доказывает, что аннотации проверяются компилятором на корректность.

В большинстве случаев автоматический вывод аннотаций и типов означают, что их не нужно указывать явно. В более сложных ситуациях аннотации времени жизни могут помочь устранить неоднозначность. Часто, особенно при создании прототипов, проще работать с собственными данными, клонируя значения там, где это необходимо.

__Времена жизни в структурах__

Если структура хранит заимствованные данные, она должна быть аннотирована временем жизни:

```rust
#[derive(Debug)]
struct Highlight<'doc>(&'doc str);

fn erase(text: String) {
    println!("Bye {text}!");
}

fn main() {
    let text = String::from("The quick brown fox jumps over the lazy dog.");
    let fox = Highlight(&text[4..19]);
    let dog = Highlight(&text[35..43]);
    // erase(text);
    println!("{fox:?}");
    println!("{dog:?}");
}
```

- аннотация `Highlight` обеспечивает, чтобы данные, хранящиеся в `&str`, существовали по крайней мере также долго, как любой экземпляр `Highlight`, использующий эти данные
- если `text` будет потреблен до окончания жизни `fox` (или `dog`), контроллер заимствований выбросит ошибку
- типы с заимствованными данными вынуждают пользователей сохранять исходные данные. Это может быть полезно для создания упрощенных представлений (lightweight views), но обычно это несколько усложняет их использование
- по возможности делайте так, чтобы структуры владели своими данными
- некоторые структуры с несколькими ссылками внутри могут иметь более одной аннотации времени жизни. Это может быть необходимо, если помимо времени жизни самой структуры, необходимо описать отношения между временами жизни самих ссылок. Это очень продвинутые варианты использования

__Упражнение: анализ Protobuf__

В этом упражнении вы создадите анализатор [двоичной кодировки protobuf](https://protobuf.dev/programming-guides/encoding/). Не волнуйтесь, это проще, чем кажется! Упражнение иллюстрирует общий шаблон парсинга данных, разделенных на фрагменты (срезы). Исходные данные никогда не копируются.

Полный анализ сообщения protobuf требует знания типов полей, индексированных по номерам полей. Обычно это описывается в файле `proto`. В этом упражнении мы закодируем эту информацию в операторы сопоставления в функциях, которые вызываются для каждого поля.

Мы будем использовать следующий прототип:

```
message PhoneNumber {
  optional string number = 1;
  optional string type = 2;
}

message Person {
  optional string name = 1;
  optional int32 id = 2;
  repeated PhoneNumber phones = 3;
}
```

Протосообщение кодируется как серия полей, идущих одно за другим. Каждый из них реализован как "тег", за которым следует значение. Тег содержит номер поля (например, `2` для поля `id` сообщения `Person`) и тип поля, определяющий, как полезная нагрузка должна извлекаться из потока байтов.

Целые числа, включая тег, представлены с помощью кодировки переменной длины, называемой `VARINT`. Функция `parse_varint` уже определена в коде. Также определены коллбеки для обработки полей `Person` и `PhoneNumber` и для парсинга сообщения в виде серии вызовов этих коллбеков.

Вам осталось реализовать функцию `parse_field` и трейт `ProtoMessage` для `Person` и `PhoneNumber`.

Обратите внимание: это упражнения является сложным и опциональным. Это означает, что на данном этапе освоения `Rust` вы можете его пропустить и вернуться к нему позже.

```rust
use std::convert::TryFrom;
use thiserror::Error;

#[derive(Debug, Error)]
enum Error {
    #[error("Invalid varint")]
    InvalidVarint,
    #[error("Invalid wire-type")]
    InvalidWireType,
    #[error("Unexpected EOF")]
    UnexpectedEOF,
    #[error("Invalid length")]
    InvalidSize(#[from] std::num::TryFromIntError),
    #[error("Unexpected wire-type)")]
    UnexpectedWireType,
    #[error("Invalid string (not UTF-8)")]
    InvalidString,
}

// Тип поля
enum WireType {
    // Тип Varint указывает, что значение является единичным `VARINT`
    Varint,
    // Тип `Len` указывает, что значение - это длина, представленная как
    // `VARINT`, точно следующий за этим количеством байтов
    Len,
    // Тип `I32` указывает, что значение - это точно 4 байта в прямом порядке (little-endian order),
    // содержащие 32-битное целое число со знаком
    I32,
    // Тип `I64` для этого упражнения не нужен
}

#[derive(Debug)]
// Значение поля, типизированное на основе типа поля
enum FieldValue<'a> {
    Varint(u64),
    // `I64(i64)` для этого упражнения не нужен
    Len(&'a [u8]),
    I32(i32),
}

#[derive(Debug)]
// Поле, содержащее номер поля и его значение
struct Field<'a> {
    field_num: u64,
    value: FieldValue<'a>,
}

trait ProtoMessage<'a>: Default + 'a {
    fn add_field(&mut self, field: Field<'a>) -> Result<(), Error>;
}

impl TryFrom<u64> for WireType {
    type Error = Error;

    fn try_from(value: u64) -> Result<WireType, Error> {
        Ok(match value {
            0 => WireType::Varint,
            // `1 => WireType::I64` для этого упражнения не нужен
            2 => WireType::Len,
            5 => WireType::I32,
            _ => return Err(Error::InvalidWireType),
        })
    }
}

impl<'a> FieldValue<'a> {
    fn as_string(&self) -> Result<&'a str, Error> {
        let FieldValue::Len(data) = self else {
            return Err(Error::UnexpectedWireType);
        };
        std::str::from_utf8(data).map_err(|_| Error::InvalidString)
    }

    fn as_bytes(&self) -> Result<&'a [u8], Error> {
        let FieldValue::Len(data) = self else {
            return Err(Error::UnexpectedWireType);
        };
        Ok(data)
    }

    fn as_u64(&self) -> Result<u64, Error> {
        let FieldValue::Varint(value) = self else {
            return Err(Error::UnexpectedWireType);
        };
        Ok(*value)
    }
}

// Функция разбора VARINT, возвращающая разобранное значение и оставшиеся байты
fn parse_varint(data: &[u8]) -> Result<(u64, &[u8]), Error> {
    for i in 0..7 {
        let Some(b) = data.get(i) else {
            return Err(Error::InvalidVarint);
        };
        if b & 0x80 == 0 {
            // Это последний байт `VARINT`, преобразуем его
            // в `u64` и возвращаем
            let mut value = 0u64;
            for b in data[..=i].iter().rev() {
                value = (value << 7) | (b & 0x7f) as u64;
            }
            return Ok((value, &data[i + 1..]));
        }
    }

    // Если байтов больше 7, значит `VARINT` не является валидным
    Err(Error::InvalidVarint)
}

// Функция преобразования тега в номер поля и тип поля
fn unpack_tag(tag: u64) -> Result<(u64, WireType), Error> {
    let field_num = tag >> 3;
    let wire_type = WireType::try_from(tag & 0x7)?;
    Ok((field_num, wire_type))
}

// Функция разбора поля, возвращающая оставшиеся байты
fn parse_field(data: &[u8]) -> Result<(Field, &[u8]), Error> {
    let (tag, remainder) = parse_varint(data)?;
    let (field_num, wire_type) = unpack_tag(tag)?;
    let (fieldvalue, remainder) = match wire_type {
        _ => todo!("На основе типа поля создаем поле, употребив столько байтов, сколько необходимо")
    };
    todo!("Возвращаем поле и оставшиеся байты")
}

// Функция разбора сообщения в определенные данные, вызывающая `T::add_field` для каждого поля.
// Все входные данные потребляются
fn parse_message<'a, T: ProtoMessage<'a>>(mut data: &'a [u8]) -> Result<T, Error> {
    let mut result = T::default();
    while !data.is_empty() {
        let parsed = parse_field(data)?;
        result.add_field(parsed.0)?;
        data = parsed.1;
    }
    Ok(result)
}

#[derive(Debug, Default)]
struct PhoneNumber<'a> {
    number: &'a str,
    type_: &'a str,
}

#[derive(Debug, Default)]
struct Person<'a> {
    name: &'a str,
    id: u64,
    phone: Vec<PhoneNumber<'a>>,
}

impl<'a> ProtoMessage<'a> for Person<'a> {
    fn add_field(&mut self, field: Field<'a>) -> Result<(), Error> {
        todo!("реализуй меня")
    }
}

impl<'a> ProtoMessage<'a> for PhoneNumber<'a> {
    fn add_field(&mut self, field: Field<'a>) -> Result<(), Error> {
        todo!("реализуй меня")
    }
}

fn main() {
    let person: Person = parse_message(&[
        0x0a, 0x07, 0x6d, 0x61, 0x78, 0x77, 0x65, 0x6c, 0x6c, 0x10, 0x2a, 0x1a,
        0x16, 0x0a, 0x0e, 0x2b, 0x31, 0x32, 0x30, 0x32, 0x2d, 0x35, 0x35, 0x35,
        0x2d, 0x31, 0x32, 0x31, 0x32, 0x12, 0x04, 0x68, 0x6f, 0x6d, 0x65, 0x1a,
        0x18, 0x0a, 0x0e, 0x2b, 0x31, 0x38, 0x30, 0x30, 0x2d, 0x38, 0x36, 0x37,
        0x2d, 0x35, 0x33, 0x30, 0x38, 0x12, 0x06, 0x6d, 0x6f, 0x62, 0x69, 0x6c,
        0x65,
    ])
    .unwrap();
    println!("{:#?}", person);
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn as_string() {
        assert!(FieldValue::Varint(10).as_string().is_err());
        assert!(FieldValue::I32(10).as_string().is_err());
        assert_eq!(FieldValue::Len(b"hello").as_string().unwrap(), "hello");
    }

    #[test]
    fn as_bytes() {
        assert!(FieldValue::Varint(10).as_bytes().is_err());
        assert!(FieldValue::I32(10).as_bytes().is_err());
        assert_eq!(FieldValue::Len(b"hello").as_bytes().unwrap(), b"hello");
    }

    #[test]
    fn as_u64() {
        assert_eq!(FieldValue::Varint(10).as_u64().unwrap(), 10u64);
        assert!(FieldValue::I32(10).as_u64().is_err());
        assert!(FieldValue::Len(b"hello").as_u64().is_err());
    }
}
```

<details>
<summary>Решение:</summary>

```rust
fn parse_field(data: &[u8]) -> Result<(Field, &[u8]), Error> {
    let (tag, remainder) = parse_varint(data)?;
    let (field_num, wire_type) = unpack_tag(tag)?;
    let (fieldvalue, remainder) = match wire_type {
        WireType::Varint => {
            let (value, remainder) = parse_varint(remainder)?;
            (FieldValue::Varint(value), remainder)
        }
        WireType::Len => {
            let (len, remainder) = parse_varint(remainder)?;
            let len: usize = len.try_into()?;
            if remainder.len() < len {
                return Err(Error::UnexpectedEOF);
            }
            let (value, remainder) = remainder.split_at(len);
            (FieldValue::Len(value), remainder)
        }
        WireType::I32 => {
            if remainder.len() < 4 {
                return Err(Error::UnexpectedEOF);
            }
            let (value, remainder) = remainder.split_at(4);
            let value = i32::from_le_bytes(value.try_into().unwrap());
            (FieldValue::I32(value), remainder)
        }
    };
    Ok((Field { field_num, value: fieldvalue }, remainder))
}

// ...

impl<'a> ProtoMessage<'a> for Person<'a> {
    fn add_field(&mut self, field: Field<'a>) -> Result<(), Error> {
        match field.field_num {
            1 => self.name = field.value.as_string()?,
            2 => self.id = field.value.as_u64()?,
            3 => self.phone.push(parse_message(field.value.as_bytes()?)?),
            _ => {} // остальное пропускаем
        }
        Ok(())
    }
}

impl<'a> ProtoMessage<'a> for PhoneNumber<'a> {
    fn add_field(&mut self, field: Field<'a>) -> Result<(), Error> {
        match field.field_num {
            1 => self.number = field.value.as_string()?,
            2 => self.type_ = field.value.as_string()?,
            _ => {} // остальное пропускаем
        }
        Ok(())
    }
}
```

</details>
