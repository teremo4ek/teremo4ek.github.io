---
title: "Rust Cookbook"
description: "Практическое руководство по Rust: алгоритмы, CLI, сжатие, параллелизм, криптография, базы данных и многое другое"
date: 2026-05-14T05:00:00Z
image: "/images/image-placeholder.png"
categories: ["Rust"]
tags: ["rust", "tutorial", "cookbook"]
series: true
---

Книга рецептов — это коллекция простых примеров, демонстрирующих хорошие практики решения распространенных задач программирования с помощью крейтов экосистемы Rust.

Для запуска примеров вам потребуется примерно такой файл Cargo.toml (версии крейтов могут отличаться):

```toml
[package]
name = "rust_cookbook"
version = "0.1.0"
edition = "2021"

[dependencies]
chrono = "0.4.31"
crossbeam = "0.8.3"
crossbeam-channel = "0.5.10"
csv = "1.3.0"
env_logger = "0.11.3"
error-chain = "0.12.4"
glob = "0.3.1"
image = "0.25.0"
lazy_static = "1.4.0"
log = "0.4.20"
mime = "0.3.17"
num = "0.4.1"
num_cpus = "1.16.0"
postgres = "0.19.7"
rand = "0.8.5"
rayon = "1.8.0"
regex = "1.10.2"
reqwest = {version = "0.11.23", features = ["blocking", "json"]}
same-file = "1.0.6"
select = "0.6.0"
serde = {version = "1.0.193", features = ["derive"]}
serde_json = "1.0.110"
threadpool = "1.8.1"
tokio = { version = "1.35.1", features = ["full"] }
unicode-segmentation = "1.10.1"
url = "2.5.0"
walkdir = "2.4.0"
dotenv = "0.15.0"
tempfile = "3.9.0"
data-encoding = "2.5.0"
ring = "0.17.7"
clap = "4.5.2"
ansi_term = "0.12.1"
flate2 = "1.0.28"
tar = "0.4.40"
semver = "1.0.22"
percent-encoding = "2.3.1"
base64 = "0.22.0"
toml = "0.8.12"
memmap = "0.7.0"

[dependencies.rusqlite]
version = "0.31.0"
features = ["bundled"]
```

Обратите внимание, что некоторые примеры работают только на Linux.
