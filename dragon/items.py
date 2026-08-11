"""Каталог предметов и магазин для Dragon Pet."""

from typing import Dict, Any

ITEMS: Dict[str, Dict[str, Any]] = {
    "meat": {
        "name": "Сочное мясо",
        "emoji": "🍖",
        "description": "Сытное угощение. Сильно снижает голод.",
        "type": "consumable",
        "effect": {"hunger": -40, "happiness": 8, "xp": 5},
        "buy_price": 25,
        "sell_price": 10,
    },
    "fish": {
        "name": "Свежая рыба",
        "emoji": "🐟",
        "description": "Лёгкая и полезная еда.",
        "type": "consumable",
        "effect": {"hunger": -25, "energy": 10, "xp": 4},
        "buy_price": 18,
        "sell_price": 7,
    },
    "berry": {
        "name": "Огненная ягода",
        "emoji": "🍒",
        "description": "Сладкая ягода, поднимает настроение.",
        "type": "consumable",
        "effect": {"hunger": -10, "happiness": 20, "xp": 3},
        "buy_price": 15,
        "sell_price": 6,
    },
    "shiny_stone": {
        "name": "Блестящий камушек",
        "emoji": "💎",
        "description": "Дракон обожает такие! Можно подарить.",
        "type": "gift",
        "effect": {"happiness": 18, "affection": 12, "xp": 10},
        "buy_price": 40,
        "sell_price": 18,
    },
    "saddle_oil": {
        "name": "Масло для седла",
        "emoji": "🧴",
        "description": "Делает седло удобнее. Бонус к полётам.",
        "type": "consumable",
        "effect": {"energy": 15, "happiness": 5, "xp": 6},
        "buy_price": 30,
        "sell_price": 12,
    },
    "dragon_scale": {
        "name": "Драконья чешуйка",
        "emoji": "🛡️",
        "description": "Редкий трофей. Даёт много опыта.",
        "type": "special",
        "effect": {"xp": 35, "affection": 5},
        "buy_price": 0,          # нельзя купить
        "sell_price": 50,
    },
    "cloud_essence": {
        "name": "Сущность облака",
        "emoji": "☁️",
        "description": "Лёгкость и свобода. Восстанавливает энергию.",
        "type": "consumable",
        "effect": {"energy": 35, "happiness": 10, "xp": 8},
        "buy_price": 45,
        "sell_price": 20,
    },
    "ancient_coin": {
        "name": "Древняя монета",
        "emoji": "🪙",
        "description": "Можно продать или коллекционировать.",
        "type": "special",
        "effect": {"xp": 15, "happiness": 5},
        "buy_price": 0,
        "sell_price": 25,
    },
    "friendship_token": {
        "name": "Токен дружбы",
        "emoji": "🤝",
        "description": "Используется для укрепления дружбы с другим драконом.",
        "type": "special",
        "effect": {},
        "buy_price": 60,
        "sell_price": 25,
    },
    "play_ball": {
        "name": "Игрушечный мяч",
        "emoji": "⚽",
        "description": "Для весёлых игр. Сильно поднимает счастье.",
        "type": "consumable",
        "effect": {"happiness": 25, "energy": -5, "xp": 7},
        "buy_price": 22,
        "sell_price": 9,
    },
}


def get_item(item_id: str) -> Dict[str, Any] | None:
    return ITEMS.get(item_id)


def format_item(item_id: str, count: int = 1) -> str:
    item = ITEMS.get(item_id)
    if not item:
        return f"❓ {item_id} ×{count}"
    return f"{item['emoji']} **{item['name']}** ×{count}"


def shop_list() -> str:
    lines = []
    for iid, item in ITEMS.items():
        if item.get("buy_price", 0) > 0:
            lines.append(
                f"{item['emoji']} `{iid}` — **{item['name']}** — {item['buy_price']} 🪙"
            )
    return "\n".join(lines) if lines else "Магазин пуст."
