"""Каталог предметов для Dragon Pet."""

from typing import Dict, Any

# id → данные предмета
ITEMS: Dict[str, Dict[str, Any]] = {
    "meat": {
        "name": "Сочное мясо",
        "emoji": "🍖",
        "description": "Сытное угощение. Сильно снижает голод.",
        "type": "consumable",
        "effect": {"hunger": -40, "happiness": 8, "xp": 5},
    },
    "fish": {
        "name": "Свежая рыба",
        "emoji": "🐟",
        "description": "Лёгкая и полезная еда.",
        "type": "consumable",
        "effect": {"hunger": -25, "energy": 10, "xp": 4},
    },
    "berry": {
        "name": "Огненная ягода",
        "emoji": "🍒",
        "description": "Сладкая ягода, поднимает настроение.",
        "type": "consumable",
        "effect": {"hunger": -10, "happiness": 20, "xp": 3},
    },
    "shiny_stone": {
        "name": "Блестящий камушек",
        "emoji": "💎",
        "description": "Дракон обожает такие! Можно подарить.",
        "type": "gift",
        "effect": {"happiness": 18, "affection": 12, "xp": 10},
    },
    "saddle_oil": {
        "name": "Масло для седла",
        "emoji": "🧴",
        "description": "Делает седло удобнее. Бонус к полётам.",
        "type": "consumable",
        "effect": {"energy": 15, "happiness": 5, "xp": 6},
    },
    "dragon_scale": {
        "name": "Драконья чешуйка",
        "emoji": "🛡️",
        "description": "Редкий трофей. Даёт много опыта.",
        "type": "special",
        "effect": {"xp": 35, "affection": 5},
    },
    "cloud_essence": {
        "name": "Сущность облака",
        "emoji": "☁️",
        "description": "Лёгкость и свобода. Восстанавливает энергию.",
        "type": "consumable",
        "effect": {"energy": 35, "happiness": 10, "xp": 8},
    },
    "ancient_coin": {
        "name": "Древняя монета",
        "emoji": "🪙",
        "description": "Можно обменять или просто коллекционировать.",
        "type": "special",
        "effect": {"xp": 15, "happiness": 5},
    },
}


def get_item(item_id: str) -> Dict[str, Any] | None:
    return ITEMS.get(item_id)


def format_item(item_id: str, count: int = 1) -> str:
    item = ITEMS.get(item_id)
    if not item:
        return f"❓ {item_id} ×{count}"
    return f"{item['emoji']} **{item['name']}** ×{count}"
