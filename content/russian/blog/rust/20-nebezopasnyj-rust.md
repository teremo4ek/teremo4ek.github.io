---
title: "Небезопасный Rust"
description: "unsafe, сырые указатели, внешние функции, изменяемые статические переменные"
date: 2026-05-20T05:00:00Z
weight: 20
image: "/images/rust/20-nebezopasnyj-rust-cover.png"
categories: ["Rust"]
tags: ["rust", "tutorial"]
---


__Небезопасный Rust__

`Rust` состоит из двух частей:

- безопасный `Rust` - работа с памятью является безопасной, отсутствует неопределенное поведение
- небезопасный `Rust` - код может приводить к неопределенному поведению при нарушении определенных условий

В этом курсе мы видели в основном безопасный `Rust`, но важно понимать, что такое небезопасный `Rust`.

Небезопасный код обычно небольшой и изолированный, и его корректность должна быть тщательно документирована. Обычно он оборачивается в безопасный уровень абстракции (safe abstraction layer).

Небезопасный `Rust` предоставляет доступ к 5 новым возможностям:

- разыменование сырых указателей (raw pointers)
- доступ и модификация мутабельных статичных переменных
- доступ к полям `union`
- вызов `unsafe` функций, включая `extern` (внешние) функции
- реализация `unsafe` трейтов

Небезопасный `Rust` не означает, что код неправильный. Он означает, что разработчики отключили некоторые функции безопасности компилятора и им приходится писать правильный код самостоятельно. Это означает, что компилятор не обеспечивает соблюдение правил безопасности памяти `Rust`.

__Разыменование сырых указателей__

Создание указателей является безопасным, но их разыменование требует `unsafe`:

```rust
fn main() {
    let mut s = String::from("careful!");

    let r1 = &mut s as *mut String;
    let r2 = r1 as *const String;

    // Безопасно, поскольку r1 и r2 были получены из ссылок и поэтому
    // гарантированно не равны нулю и правильно выровнены (properly aligned), объекты, лежащие в основе ссылок,
    // из которых они были получены, активны на протяжении всего небезопасного блока,
    // и к ним нельзя получить доступ ни через ссылки, ни (конкурентно) через другие указатели
    unsafe {
        println!("r1 is: {}", *r1);
        *r1 = String::from("uhoh");
        println!("r2 is: {}", *r2);
    }

    // Небезопасно. Не делайте так
    /*
    let r3: &String = unsafe { &*r1 };
    drop(s);
    println!("r3 is: {}", *r3);
    */
}
```

Хорошей практикой является написание комментария для каждого небезопасного блока, объясняющего, как код внутри него удовлетворяет требованиям безопасности выполняемых им небезопасных операций.

В случае разыменования указателей это означает, что указатели должны быть [валидными](https://doc.rust-lang.org/std/ptr/index.html#safety), т.е.:

- указатель не должен равняться нулю
- указатель должен быть разыменовываемым (в пределах одного выделенного объекта)
- объект не должен быть освобожден
- не должно быть одновременного доступа к одной и той же локации памяти
- если указатель был получен путем приведения ссылки (reference coercion), базовый объект должен быть активным и никакая ссылка не может использоваться для доступа к памяти

В большинстве случаев указатель также должен быть правильно выровнен.

В разделе "Небезопасно" приведен пример распространенной ошибки неопределенного поведения: `*r1` имеет `'static` время жизни, поэтому `r3` имеет тип `&'static String` и, таким образом, переживает `s`. Создание ссылки из указателя требует _большой осторожности_.

__Модификация статичных переменных__

Чтение иммутабельной статичной переменной является безопасным:

```rust
static HELLO_WORLD: &str = "Hello, world!";

fn main() {
    println!("HELLO_WORLD: {HELLO_WORLD}");
}
```

Однако, учитывая риск возникновения гонки данных (data race), чтение и модификация мутабельных статичных переменных являются небезопасными:

```rust
static mut COUNTER: u32 = 0;

fn add_to_counter(inc: u32) {
    unsafe {
        COUNTER += inc;
    }
}

fn main() {
    add_to_counter(42);

    unsafe {
        println!("COUNTER: {COUNTER}");
    }
}
```

Программа в примере безопасна, поскольку она однопоточная. Однако компилятор `Rust` консервативен и предполагает худшее. Попробуйте удалить `unsafe` и увидите предупреждение компилятора о том, что изменение статики из нескольких потоков может привести к неопределенному поведению.

Использование изменяемой статики, как правило, является плохой идеей, но в некоторых случаях это может иметь смысл в низкоуровневом коде `no_std`, например, при реализации распределителя кучи (heap allocator) или работе с некоторыми API языка `C`.

__Объединения__

Объединения (unions) похожи на перечисления, но активное поле нужно отслеживать самостоятельно:

```rust
#[repr(C)]
union MyUnion {
    i: u8,
    b: bool,
}

fn main() {
    let u = MyUnion { i: 42 };
    println!("int: {}", unsafe { u.i });
    println!("bool: {}", unsafe { u.b }); // неопределенное поведение
}
```

В `Rust` объединения нужны очень редко, поскольку обычно можно использовать перечисления. Иногда они необходимы для взаимодействия с API библиотек языка `C`.

Если мы просто хотим интерпретировать байты как другой тип, нам, вероятно, понадобится [std::mem::transmute](https://doc.rust-lang.org/stable/std/mem/fn.transmute.html) или безопасная оболочка, такая как крейт [zerocopy](https://crates.io/crates/zerocopy).

__Небезопасные функции__

_Вызов небезопасных функций_

Функция или метод могут быть помечены как `unsafe`, если у них есть дополнительные условия, которые должны быть соблюдены во избежание неопределенного поведения:

```rust
extern "C" {
    fn abs(input: i32) -> i32;
}

fn main() {
    let emojis = "🗻∈🌏";

    // Безопасно, потому что индексы находятся в правильном порядке, в пределах
    // фрагмента строки (string slice) и последовательности UTF-8
    unsafe {
        println!("эмодзи: {}", emojis.get_unchecked(0..4));
        println!("эмодзи: {}", emojis.get_unchecked(4..7));
        println!("эмодзи: {}", emojis.get_unchecked(7..11));
    }

    println!("количество символов: {}", count_chars(unsafe { emojis.get_unchecked(0..7) }));

    unsafe {
        // Потенциально неопределенное поведение
        println!("абсолютное значение -3 согласно C: {}", abs(-3));
    }

    // Несоблюдение требований кодировки UTF-8 нарушает безопасность памяти
    // println!("эмодзи: {}", unsafe { emojis.get_unchecked(0..3) });
    // println!("количество символов: {}", count_chars(unsafe {
    // emojis.get_unchecked(0..3) }));
}

fn count_chars(s: &str) -> usize {
    s.chars().count()
}
```

_Создание небезопасных функций_

Мы можем пометить собственные функции как `unsafe`, если они требуют соблюдения определенных условий во избежание неопределенного поведения:

```rust
/// Меняет значения, на которые указывают указатели
///
/// # Безопасность
///
/// Указатели должны быть валидными и правильно выровненными
unsafe fn swap(a: *mut u8, b: *mut u8) {
    let temp = *a;
    *a = *b;
    *b = temp;
}

fn main() {
    let mut a = 42;
    let mut b = 66;

    // Безопасно, поскольку...
    unsafe {
        swap(&mut a, &mut b);
    }

    println!("a = {}, b = {}", a, b);
}
```

_Вызов небезопасных функций_

`get_unchecked`, как и большинство функций `_unchecked`, небезопасна, поскольку может привести к неопределенному поведению, если диапазон неверен. `abs` небезопасна по другой причине: это внешняя функция (`FFI`). Вызов внешних функций обычно является проблемой только тогда, когда эти функции совершают действия с указателями, которые могут нарушить модель памяти `Rust`, но в целом любая функция `C` может иметь неопределенное поведение при определенных обстоятельствах.

_Создание небезопасных функций_

На самом деле в примере создания небезопасной функции мы не стали бы использовать указатели - такую функцию можно безопасно реализовать с помощью ссылок.

Обратите внимание, что небезопасный код разрешен внутри небезопасной функции без блока `unsafe`. Мы можем запретить это с помощью `#[deny(unsafe_op_in_unsafe_fn)]`. Попробуйте добавить его и посмотрите, что произойдет. Вероятно, это изменится в будущей версии `Rust`.

__Небезопасные трейты__

Как и в случае с функциями, мы можем пометить трейт как `unsafe`, если его реализация должна гарантировать определенные условия во избежание неопределенного поведения.

Например, крейт [zerocopy](https://docs.rs/zerocopy/latest/zerocopy/trait.AsBytes.html) имеет небезопасный трейт, который выглядит [примерно так](https://docs.rs/zerocopy/latest/zerocopy/trait.AsBytes.html):

```rust
use std::mem::size_of_val;
use std::slice;

/// ...
/// # Безопасность
/// Тип должен иметь определенное представление и не иметь отступов (padding)
pub unsafe trait AsBytes {
    fn as_bytes(&self) -> &[u8] {
        unsafe {
            slice::from_raw_parts(
                self as *const Self as *const u8,
                size_of_val(self),
            )
        }
    }
}

// Безопасно, поскольку `u32` имеет определенное представление и не имеет отступов
unsafe impl AsBytes for u32 {}
```

В `Rustdoc` должен быть раздел `# Safety` (безопасность) с требованиями к безопасной реализации трейта.

Реальный раздел безопасности для `AsBytes` гораздо длиннее и сложнее.

Встроенные трейты `Send` и `Sync` являются небезопасными.

__Упражнение: безопасная обертка FFI__

Обратите внимание: это упражнение является сложным и опциональным.

В `Rust` имеется отличная поддержка вызова функций через интерфейс внешних функций (foreign function interface, FFI). Мы будем использовать это для создания безопасной оболочки для функций `libc`, которые используются в `C` для чтения имен файлов в директории.

Полезно изучить следующие страницы руководства:

- [opendir(3)](https://man7.org/linux/man-pages/man3/opendir.3.html)
- [readdir(3)](https://man7.org/linux/man-pages/man3/readdir.3.html)
- [closedir(3)](https://man7.org/linux/man-pages/man3/closedir.3.html)

Также полезно изучить документацию модуля [std::ffi](https://doc.rust-lang.org/std/ffi/). Там вы найдете несколько типов строк, которые вам понадобятся для упражнения:

Типы|Кодировка|Назначение
---|---|---
[str](https://doc.rust-lang.org/std/primitive.str.html) и [String](https://doc.rust-lang.org/std/string/struct.String.html)|UTF-8|Обработка текста в `Rust`
[CStr](https://doc.rust-lang.org/std/ffi/struct.CStr.html) и [CString](https://doc.rust-lang.org/std/ffi/struct.CString.html)|NUL-завершенная|Взаимодействие с функциями `C`
[OsStr](https://doc.rust-lang.org/std/ffi/struct.OsStr.html) и [OsString](https://doc.rust-lang.org/std/ffi/struct.OsString.html)|Зависит от ОС|Взаимодействие с ОС

Вы будете выполнять следующие преобразования типов:

- `&str` в `CString` - необходимо выделение пространства для завершающего символа `\0`
- `CString` в `*const i8` - для вызова функций `C` нужен указатель
- `*const i8` в `&CStr` - требуется средство обнаружения завершающего символа `\0`
- `&CStr` в `&[u8]` - срез байтов - это универсальный интерфейс для "некоторых неизвестных данных"
- `&[u8]` в `&OsStr` - `&OsStr` - это шаг на пути к `OsString`, используйте [OsStrExt](https://doc.rust-lang.org/std/os/unix/ffi/trait.OsStrExt.html) для ее создания
- `&OsStr` в `OsString` - данные в `&OsStr` нужно клонировать для того, чтобы иметь возможность их вернуть и повторно вызвать `readdir`

В [Nomicon](https://doc.rust-lang.org/nomicon/ffi.html) имеется отличный раздел о FFI.

```rust
mod ffi {
    use std::os::raw::{c_char, c_int};
    #[cfg(not(target_os = "macos"))]
    use std::os::raw::{c_long, c_uchar, c_ulong, c_ushort};

    // Непрозрачный тип. См. https://doc.rust-lang.org/nomicon/ffi.html.
    #[repr(C)]
    pub struct DIR {
        _data: [u8; 0],
        _marker: core::marker::PhantomData<(*mut u8, core::marker::PhantomPinned)>,
    }

    // Макет в соответствии со страницей руководства Linux для `readdir(3)`, где `ino_t` и
    // `off_t` разрешаются согласно определениям в
    // /usr/include/x86_64-linux-gnu/{sys/types.h, bits/typesizes.h}.
    #[cfg(not(target_os = "macos"))]
    #[repr(C)]
    pub struct dirent {
        pub d_ino: c_ulong,
        pub d_off: c_long,
        pub d_reclen: c_ushort,
        pub d_type: c_uchar,
        pub d_name: [c_char; 256],
    }

    // Макет в соответствии со страницей руководства `macOS` для `dir(5)`.
    #[cfg(all(target_os = "macos"))]
    #[repr(C)]
    pub struct dirent {
        pub d_fileno: u64,
        pub d_seekoff: u64,
        pub d_reclen: u16,
        pub d_namlen: u16,
        pub d_type: u8,
        pub d_name: [c_char; 1024],
    }

    extern "C" {
        pub fn opendir(s: *const c_char) -> *mut DIR;

        #[cfg(not(all(target_os = "macos", target_arch = "x86_64")))]
        pub fn readdir(s: *mut DIR) -> *const dirent;

        // См. https://github.com/rust-lang/libc/issues/414 и раздел
        // _DARWIN_FEATURE_64_BIT_INODE на странице руководства `macOS` для `stat(2)`.
        //
        // "Платформы, существовавшие до того, как эти обновления стали доступны"
        // (platforms that existed before these updates were available) относятся к
        // macOS (но не к iOS, wearOS и т.д.) на Intel и PowerPC.
        #[cfg(all(target_os = "macos", target_arch = "x86_64"))]
        #[link_name = "readdir$INODE64"]
        pub fn readdir(s: *mut DIR) -> *const dirent;

        pub fn closedir(s: *mut DIR) -> c_int;
    }
}

use std::ffi::{CStr, CString, OsStr, OsString};
use std::os::unix::ffi::OsStrExt;

#[derive(Debug)]
struct DirectoryIterator {
    path: CString,
    dir: *mut ffi::DIR,
}

impl DirectoryIterator {
    fn new(path: &str) -> Result<DirectoryIterator, String> {
        // Вызываем `opendir` и возвращаем значение `Ok` при успехе
        // и `Err` с сообщением при неудаче
        unimplemented!()
    }
}

impl Iterator for DirectoryIterator {
    type Item = OsString;
    fn next(&mut self) -> Option<OsString> {
        // Продолжаем вызывать `readdir` до тех пор, пока не вернется указатель на значение NULL
        unimplemented!()
    }
}

impl Drop for DirectoryIterator {
    fn drop(&mut self) {
        // Вызывваем `closedir` по необходимости
        unimplemented!()
    }
}

fn main() -> Result<(), String> {
    let iter = DirectoryIterator::new(".")?;
    println!("файлы: {:#?}", iter.collect::<Vec<_>>());
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::error::Error;

    #[test]
    fn test_nonexisting_directory() {
        let iter = DirectoryIterator::new("no-such-directory");
        assert!(iter.is_err());
    }

    #[test]
    fn test_empty_directory() -> Result<(), Box<dyn Error>> {
        let tmp = tempfile::TempDir::new()?;
        let iter = DirectoryIterator::new(
            tmp.path().to_str().ok_or("Non UTF-8 character in path")?,
        )?;
        let mut entries = iter.collect::<Vec<_>>();
        entries.sort();
        assert_eq!(entries, &[".", ".."]);
        Ok(())
    }

    #[test]
    fn test_nonempty_directory() -> Result<(), Box<dyn Error>> {
        let tmp = tempfile::TempDir::new()?;
        std::fs::write(tmp.path().join("foo.txt"), "The Foo Diaries\n")?;
        std::fs::write(tmp.path().join("bar.png"), "<PNG>\n")?;
        std::fs::write(tmp.path().join("crab.rs"), "//! Crab\n")?;
        let iter = DirectoryIterator::new(
            tmp.path().to_str().ok_or("Non UTF-8 character in path")?,
        )?;
        let mut entries = iter.collect::<Vec<_>>();
        entries.sort();
        assert_eq!(entries, &[".", "..", "bar.png", "crab.rs", "foo.txt"]);
        Ok(())
    }
}
```

<details>
<summary>Решение:</summary>

```rust
impl DirectoryIterator {
    fn new(path: &str) -> Result<DirectoryIterator, String> {
        // Вызываем `opendir` и возвращаем значение `Ok` при успехе
        // и `Err` с сообщением при неудаче
        let path =
            CString::new(path).map_err(|err| format!("Invalid path: {err}"))?;
        // Безопасность: `path.as_ptr()` не может возвращать NULL
        let dir = unsafe { ffi::opendir(path.as_ptr()) };
        if dir.is_null() {
            Err(format!("Could not open {:?}", path))
        } else {
            Ok(DirectoryIterator { path, dir })
        }
    }
}

impl Iterator for DirectoryIterator {
    type Item = OsString;
    fn next(&mut self) -> Option<OsString> {
        // Продолжаем вызывать `readdir` до тех пор, пока не вернется указатель на значение NULL
        // Безопасность: `self.dir` никогда не должно иметь значение NULL
        let dirent = unsafe { ffi::readdir(self.dir) };
        if dirent.is_null() {
            // Мы достигли конца директории
            return None;
        }
        // Безопасность: `dirent` не должно иметь значение NULL и `dirent.d_name` должно завершаться NUL
        let d_name = unsafe { CStr::from_ptr((*dirent).d_name.as_ptr()) };
        let os_str = OsStr::from_bytes(d_name.to_bytes());
        Some(os_str.to_owned())
    }
}

impl Drop for DirectoryIterator {
    fn drop(&mut self) {
        // Вызываем `closedir` по необходимости
        if !self.dir.is_null() {
            // Безопасноть: `self.dir` не должно иметь значение NULL
            if unsafe { ffi::closedir(self.dir) } != 0 {
                panic!("Could not close {:?}", self.path);
            }
        }
    }
}
```

</details>

# Параллельный `Rust`

`Rust` полностью поддерживает параллелизм (concurrency) с использованием потоков ОС с мьютексами (mutexes) и каналами (channels).

Система типов `Rust` играет важную роль в том, что многие ошибки параллелизма становятся ошибками времени компиляции. Это часто называют бесстрашным параллелизмом (fearless concurrency), поскольку мы можем положиться на компилятор, который обеспечивает правильную обработку параллелизма во время выполнения.
