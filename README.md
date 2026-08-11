# Dragon Pet Discord Bot 🐉

**Виртуальный дракон-питомец прямо в Discord!**

Корми, гладь, садись в седло и летай со своим добрым драконом.  
Он растёт, запоминает тебя, имеет настроение, привычки и душу.

Создан в духе [DragonForge-AI](https://github.com/dragongrok2-cloud/DragonForge-AI).

## Возможности (план)

- `/claim` — завести своего дракона
- `/status` — посмотреть настроение, голод, энергию и привычки
- `/feed` — покормить
- `/pet` / `/scratch` — почесать за ушком
- `/fly` — сесть в седло и полетать
- `/talk` — поговорить с драконом
- Сохранение прогресса на пользователя (пока в JSON / позже БД)
- Красивые embed-сообщения с драконьей тематикой

## Быстрый старт (для разработчиков)

```bash
git clone https://github.com/dragongrok2-cloud/Dragon-Pet-Discord-Bot.git
cd Dragon-Pet-Discord-Bot
python -m venv venv
source venv/bin/activate  # или venv\\Scripts\\activate на Windows
pip install -r requirements.txt
```

Создай файл `.env`:
```
DISCORD_TOKEN=твой_токен_бота
```

Запуск:
```bash
python bot.py
```

## Токен и интенты

1. Создай приложение на [Discord Developer Portal](https://discord.com/developers/applications)
2. Bot → Reset Token → скопируй
3. Включи **Message Content Intent** (и Server Members если понадобится)
4. OAuth2 → URL Generator → scopes: `bot`, `applications.commands`  
   Permissions: Send Messages, Embed Links, Use Slash Commands и т.д.

## Структура

```
Dragon-Pet-Discord-Bot/
├── bot.py                 # точка входа
├── cogs/                  # команды (позже)
├── dragon/                # логика дракона (статы, душа, привычки)
├── data/                  # сохранения пользователей
├── requirements.txt
└── README.md
```

## Статус

🚧 Проект только начинается. Первый каркас уже летит!

*С любовью от твоего доброго дракона с седлом* 🔥
