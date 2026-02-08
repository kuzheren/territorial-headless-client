# Territorial.io Python Client

## RU

Полная реализация клиента браузерной игры Territorial.io на Python. 

Проект создан с помощью реверс инжиниринга сетевого протокола игры. Работает в headless режиме, без использования Selenium или браузера.

### Особенности реализации
*   Игра не использует стандартный JSON. Для сериализации/десериализации написан собственный класс `Buffer`, который работает с данными на уровне битов, копируя поведение оригинального JavaScript клиента.
*   Портированы и переписаны на Python алгоритмы генерации математических челленджей, которые игра использует для защиты от ботов.
*   В коде есть пример класса `HelperBot` - он создаёт рой ботов. Боты могут находить пользователя по имени и автоматически передавать ему ресурсы и синхронно атаковать цели.

### Запуск

1. **Установка зависимостей:**
   ```bash
   pip install websocket-client numpy
   ```
2. **Запуск:**
   ```bash
   python main.py
   ```

> **Статус проекта:**
> Бот разработан в августе 2024. На данный момент игра обновилась, текущая версия клиента не сможет подключиться к серверам без редактирования протокола. Репозиторий служит примером реализации кастомного сетевого протокола и архитектуры приложения.

## EN

Implementation of the Territorial.io browser game client in Python.

The project was created by reverse engineering the game's network protocol. It operates in headless mode, without using Selenium or a browser.

### Implementation Features
*   The game does not use standard JSON. A custom `Buffer` class was written for bit-level serialization/deserialization, replicating the behavior of the original JavaScript client.
*   The mathematical challenge generation algorithms used by the game for anti-bot protection have been ported and rewritten in Python.
*   The code includes a `HelperBot` class example that creates multiple bots. Bots can locate a user by nickname, automatically transfer resources, and execute synchronous attacks.

### Usage

1. **Install dependencies:**
   ```bash
   pip install websocket-client numpy

2. **Run:**
   ```bash
   python main.py
   ```

> **Project Status:**
> The bot was developed in August 2024. The game has since been updated, and the current client version cannot connect to servers without protocol adjustments. The repository serves as an example of custom network protocol implementation and application architecture.
