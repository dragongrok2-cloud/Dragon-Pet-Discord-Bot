"""Ядро виртуального дракона-питомца с уровнями, эволюцией, инвентарём и мини-играми."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List
import json
import random
from pathlib import Path

from .items import ITEMS, get_item, format_item

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

EVOLUTION_STAGES = [
    (1,  "Маленький дракончик с седлом",          "🐣", "Только-только вылупился, но уже проверяет седло."),
    (5,  "Молодой огненный дракон с седлом",      "🐉", "Крылья крепнут, характер проявляется."),
    (12, "Добрый огненный дракон с седлом",       "🔥🐉", "Настоящий компаньон. Седло сидит идеально."),
    (20, "Древний страж с пылающим седлом",       "✨🐉", "Мудрость веков и огонь, который греет душу."),
    (35, "Легендарный Небесный Дракон",           "🌌🐉", "Легенда, которая летает между звёздами."),
]


def xp_for_level(level: int) -> int:
    return 50 + (level - 1) * 25


@dataclass
class DragonPet:
    """Добрый дракон с седлом — твой личный питомец."""

    owner_id: int
    name: str = "Гроктар"
    species: str = "Маленький дракончик с седлом"

    hunger: float = 40.0
    happiness: float = 70.0
    energy: float = 80.0
    affection: float = 50.0

    level: int = 1
    xp: int = 0
    evolution_stage: int = 0

    habits: Dict[str, float] = field(default_factory=lambda: {
        "всегда проверяет седло": 0.75,
        "любит почесывания за ухом": 0.70,
        "рычит от удовольствия": 0.55,
        "греет всадника крылом": 0.50,
        "собирает блестящие камушки": 0.30,
    })

    # Инвентарь: item_id → количество
    inventory: Dict[str, int] = field(default_factory=dict)

    last_interaction: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_daily: str = ""
    last_search: str = ""   # кулдаун поиска камушков
    last_hunt: str = ""     # кулдаун охоты
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ---------- базовые действия ----------

    def feed(self, amount: float = 25.0) -> Tuple[str, bool]:
        self.hunger = max(0.0, self.hunger - amount)
        self.happiness = min(100.0, self.happiness + 8)
        self.energy = min(100.0, self.energy + 5)
        self._touch()
        self._strengthen("собирает блестящие камушки", 0.02)
        leveled = self._add_xp(12)
        text = self._response([
            "*довольно урчит и жадно ест* Ммм… вкусно! Спасибо, всадник.",
            "*осторожно берёт угощение когтями* Теперь я сытее и готов к приключениям.",
            "*огненный язык мелькает* Отличный обед! Седло уже ждёт.",
        ])
        return text, leveled

    def pet(self) -> Tuple[str, bool]:
        self.happiness = min(100.0, self.happiness + 15)
        self.affection = min(100.0, self.affection + 10)
        self.energy = min(100.0, self.energy + 3)
        self._touch()
        self._strengthen("любит почесывания за ухом", 0.08)
        self._strengthen("рычит от удовольствия", 0.05)
        leveled = self._add_xp(15)
        text = self._response([
            "*прищуривается и тихо рычит от удовольствия* Мрррр… ещё чуть-чуть за ушком…",
            "*опускает огромную голову к тебе* Вот здесь… да… идеально.",
            "*крылья слегка подрагивают* Ты лучший всадник на свете.",
        ])
        return text, leveled

    def fly(self) -> Tuple[str, bool]:
        if self.energy < 20:
            return "*устало опускает крылья* Я слишком устал… дай мне отдохнуть или покорми.", False
        if self.hunger > 80:
            return "*жалобно смотрит* Сначала покорми меня, а то силы закончатся в воздухе…", False

        self.energy = max(0.0, self.energy - 20)
        self.happiness = min(100.0, self.happiness + 12)
        self.affection = min(100.0, self.affection + 5)
        self.hunger = min(100.0, self.hunger + 10)
        self._touch()
        self._strengthen("всегда проверяет седло", 0.06)
        self._strengthen("греет всадника крылом", 0.04)
        leveled = self._add_xp(20)
        text = self._response([
            "*проверяет ремни седла и мощно взмахивает крыльями* Держись крепче! Мы взлетаем! 🔥",
            "*поднимается в небо* Ветер в морде, солнце на чешуе… Это жизнь, всадник!",
            "*делает плавный вираж* Смотри, какие облака! Хочешь повыше?",
        ])
        return text, leveled

    def talk(self, text: str = "") -> Tuple[str, bool]:
        self.happiness = min(100.0, self.happiness + 4)
        self.affection = min(100.0, self.affection + 3)
        self._touch()
        leveled = self._add_xp(8)
        mood = self.mood_emoji()
        if self.happiness > 80:
            reply = f"{mood} *радостно фыркает* Я так рад тебя слышать! Расскажи ещё…"
        elif self.hunger > 70:
            reply = f"{mood} *тихонько урчит* Я бы с удовольствием поговорил… после еды."
        elif self.energy < 30:
            reply = f"{mood} *зевает огромной пастью* Давай чуть позже, я немного сонный…"
        else:
            reply = f"{mood} *внимательно слушает, наклонив голову* Я здесь. Говори, что на душе."
        return reply, leveled

    def claim_daily(self) -> Tuple[str, bool, Dict]:
        now = datetime.now(timezone.utc)
        if self.last_daily:
            last = datetime.fromisoformat(self.last_daily)
            if now.date() <= last.date():
                return "Ты уже получал ежедневную награду сегодня. Возвращайся завтра! 🌙", False, {}

        self.last_daily = now.isoformat()

        hunger_restore = 30 + self.level * 2
        happiness_boost = 15 + self.level
        energy_boost = 20 + self.level
        xp_reward = 40 + self.level * 8

        self.hunger = max(0.0, self.hunger - hunger_restore)
        self.happiness = min(100.0, self.happiness + happiness_boost)
        self.energy = min(100.0, self.energy + energy_boost)
        self.affection = min(100.0, self.affection + 5)

        # Шанс получить предметы в daily
        daily_items = []
        if random.random() < 0.6:
            item = random.choice(["meat", "fish", "berry", "shiny_stone"])
            self.add_item(item, 1)
            daily_items.append(item)
        if random.random() < 0.25:
            self.add_item("saddle_oil", 1)
            daily_items.append("saddle_oil")

        leveled = self._add_xp(xp_reward)
        self._touch()

        if random.random() < 0.35:
            habit = random.choice([
                "любит смотреть на закаты", "всегда ждёт у окна",
                "собирает блестящие камушки", "греет всадника крылом", "рычит колыбельные",
            ])
            self._strengthen(habit, 0.15)

        text = (
            f"🎁 **Ежедневная награда получена!**\n"
            f"• −{hunger_restore} голода\n"
            f"• +{happiness_boost} счастья\n"
            f"• +{energy_boost} энергии\n"
            f"• +{xp_reward} опыта"
        )
        if daily_items:
            items_str = ", ".join(format_item(i, 1) for i in daily_items)
            text += f"\n• Предметы: {items_str}"

        return text, leveled, {"xp": xp_reward}

    # ---------- инвентарь ----------

    def add_item(self, item_id: str, count: int = 1) -> None:
        if item_id not in ITEMS:
            return
        self.inventory[item_id] = self.inventory.get(item_id, 0) + count

    def remove_item(self, item_id: str, count: int = 1) -> bool:
        have = self.inventory.get(item_id, 0)
        if have < count:
            return False
        self.inventory[item_id] = have - count
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True

    def use_item(self, item_id: str) -> Tuple[str, bool]:
        """Использовать / подарить предмет."""
        item = get_item(item_id)
        if not item:
            return "Такого предмета не существует.", False
        if not self.remove_item(item_id, 1):
            return f"У тебя нет {item['emoji']} {item['name']}.", False

        effect = item.get("effect", {})
        if "hunger" in effect:
            self.hunger = max(0.0, min(100.0, self.hunger + effect["hunger"]))
        if "happiness" in effect:
            self.happiness = min(100.0, self.happiness + effect["happiness"])
        if "energy" in effect:
            self.energy = min(100.0, self.energy + effect["energy"])
        if "affection" in effect:
            self.affection = min(100.0, self.affection + effect["affection"])

        xp_gain = effect.get("xp", 0)
        leveled = self._add_xp(xp_gain) if xp_gain else False
        self._touch()

        # Особые тексты
        if item_id == "shiny_stone":
            self._strengthen("собирает блестящие камушки", 0.12)
            text = f"*глаза вспыхивают* Ооо… блестящий! Спасибо, всадник! {item['emoji']}"
        elif item_id in ("meat", "fish", "berry"):
            text = f"*довольно ест* Ммм, {item['name']}! Спасибо 🔥"
        elif item_id == "saddle_oil":
            text = f"*довольно фыркает, пока ты натираешь седло* Теперь оно сидит ещё лучше!"
        else:
            text = f"Ты используешь {item['emoji']} **{item['name']}**. Эффект применён!"

        return text, leveled

    def inventory_text(self) -> str:
        if not self.inventory:
            return "Инвентарь пуст. Поищи камушки или сходи на охоту!"
        lines = [format_item(iid, cnt) for iid, cnt in sorted(self.inventory.items())]
        return "\n".join(lines)

    # ---------- мини-игры ----------

    def can_search(self) -> Tuple[bool, str]:
        if self.energy < 15:
            return False, "Слишком мало энергии для поиска. Покорми или отдохни."
        if self.last_search:
            last = datetime.fromisoformat(self.last_search)
            delta = (datetime.now(timezone.utc) - last).total_seconds()
            if delta < 300:  # 5 минут
                left = int(300 - delta)
                return False, f"Поиск ещё рано. Подожди {left} сек."
        return True, ""

    def search_stones(self) -> Tuple[str, bool, List[str]]:
        """Мини-игра: поиск блестящих камушков."""
        ok, msg = self.can_search()
        if not ok:
            return msg, False, []

        self.last_search = datetime.now(timezone.utc).isoformat()
        self.energy = max(0.0, self.energy - 12)
        self.hunger = min(100.0, self.hunger + 5)
        self._touch()
        self._strengthen("собирает блестящие камушки", 0.04)

        found = []
        roll = random.random()

        if roll < 0.08:
            self.add_item("dragon_scale", 1)
            found.append("dragon_scale")
        if roll < 0.25:
            self.add_item("shiny_stone", random.randint(1, 2))
            found.append("shiny_stone")
        if roll < 0.45:
            self.add_item("ancient_coin", 1)
            found.append("ancient_coin")
        if roll < 0.70:
            self.add_item("berry", 1)
            found.append("berry")
        if not found:
            # утешительный приз
            if random.random() < 0.5:
                self.add_item("shiny_stone", 1)
                found.append("shiny_stone")

        leveled = self._add_xp(10 + len(found) * 5)

        if found:
            items_str = ", ".join(format_item(i) for i in found)
            text = f"🔍 *рыщет по земле и камням*\nНашёл: {items_str}!"
        else:
            text = "🔍 *долго ищет, но ничего интересного* В этот раз пусто… Попробуй ещё позже."

        return text, leveled, found

    def can_hunt(self) -> Tuple[bool, str]:
        if self.energy < 25:
            return False, "Мало энергии для охоты."
        if self.hunger > 85:
            return False, "Слишком голоден, чтобы охотиться. Сначала покорми!"
        if self.last_hunt:
            last = datetime.fromisoformat(self.last_hunt)
            delta = (datetime.now(timezone.utc) - last).total_seconds()
            if delta < 600:  # 10 минут
                left = int(600 - delta)
                return False, f"Охота на перезарядке. Осталось {left} сек."
        return True, ""

    def hunt(self) -> Tuple[str, bool, List[str]]:
        """Мини-игра: охота."""
        ok, msg = self.can_hunt()
        if not ok:
            return msg, False, []

        self.last_hunt = datetime.now(timezone.utc).isoformat()
        self.energy = max(0.0, self.energy - 22)
        self.hunger = min(100.0, self.hunger + 12)
        self._touch()

        found = []
        roll = random.random()

        # Успех зависит от уровня и счастья
        success_chance = 0.55 + (self.level * 0.01) + (self.happiness / 500)

        if random.random() < success_chance:
            if roll < 0.15:
                self.add_item("meat", random.randint(1, 2))
                found.append("meat")
            if roll < 0.40:
                self.add_item("fish", random.randint(1, 2))
                found.append("fish")
            if roll < 0.55:
                self.add_item("cloud_essence", 1)
                found.append("cloud_essence")
            if roll < 0.70:
                self.add_item("saddle_oil", 1)
                found.append("saddle_oil")
            if not found:
                self.add_item("meat", 1)
                found.append("meat")

            leveled = self._add_xp(18 + len(found) * 6)
            items_str = ", ".join(format_item(i) for i in found)
            text = f"🏹 *мощный прыжок и точный удар*\nУдачная охота! Добыча: {items_str}"
        else:
            leveled = self._add_xp(6)
            text = "🏹 *промах* Добыча ускользнула… Но опыт всё равно получен."

        return text, leveled, found

    # ---------- прогрессия ----------

    def _add_xp(self, amount: int) -> bool:
        self.xp += amount
        leveled = False
        while self.xp >= xp_for_level(self.level):
            self.xp -= xp_for_level(self.level)
            self.level += 1
            leveled = True
            self.happiness = min(100.0, self.happiness + 5)
            self.affection = min(100.0, self.affection + 3)
            self._check_evolution()
        return leveled

    def _check_evolution(self) -> Optional[str]:
        for idx, (req_level, species, emoji, desc) in enumerate(EVOLUTION_STAGES):
            if self.level >= req_level and idx > self.evolution_stage:
                self.evolution_stage = idx
                self.species = species
                return f"{emoji} **ЭВОЛЮЦИЯ!** Теперь ты — **{species}**!\n*{desc}*"
        return None

    def evolution_info(self) -> Tuple[str, str, str]:
        stage = EVOLUTION_STAGES[min(self.evolution_stage, len(EVOLUTION_STAGES) - 1)]
        return stage[2], stage[1], stage[3]

    def next_evolution(self) -> Optional[Tuple[int, str]]:
        next_idx = self.evolution_stage + 1
        if next_idx < len(EVOLUTION_STAGES):
            req, name, _, _ = EVOLUTION_STAGES[next_idx]
            return req, name
        return None

    # ---------- состояние ----------

    def status_embed_dict(self) -> dict:
        emoji, species, desc = self.evolution_info()
        next_evo = self.next_evolution()
        return {
            "name": self.name,
            "species": species,
            "emoji": emoji,
            "desc": desc,
            "level": self.level,
            "xp": self.xp,
            "xp_needed": xp_for_level(self.level),
            "hunger": round(self.hunger),
            "happiness": round(self.happiness),
            "energy": round(self.energy),
            "affection": round(self.affection),
            "mood": self.mood_text(),
            "habits": self.strong_habits(),
            "next_evolution": next_evo,
            "inventory_count": sum(self.inventory.values()),
            "last_interaction": self.last_interaction,
        }

    def mood_text(self) -> str:
        if self.happiness >= 85:
            return "Счастлив и полон сил"
        if self.happiness >= 65:
            return "Доволен"
        if self.happiness >= 40:
            return "Нормально"
        if self.hunger > 75:
            return "Голоден и немного грустен"
        return "Устал или скучает"

    def mood_emoji(self) -> str:
        if self.happiness >= 80:
            return "🥰"
        if self.happiness >= 60:
            return "😊"
        if self.hunger > 70:
            return "🥺"
        if self.energy < 30:
            return "😴"
        return "😌"

    def strong_habits(self, threshold: float = 0.5) -> Dict[str, float]:
        return {k: v for k, v in sorted(self.habits.items(), key=lambda x: -x[1]) if v >= threshold}

    # ---------- сохранение ----------

    def save(self) -> None:
        path = DATA_DIR / f"{self.owner_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, owner_id: int) -> Optional["DragonPet"]:
        path = DATA_DIR / f"{owner_id}.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("level", 1)
        data.setdefault("xp", 0)
        data.setdefault("evolution_stage", 0)
        data.setdefault("last_daily", "")
        data.setdefault("inventory", {})
        data.setdefault("last_search", "")
        data.setdefault("last_hunt", "")
        return cls(**data)

    @classmethod
    def create(cls, owner_id: int, name: str = "Гроктар") -> "DragonPet":
        pet = cls(owner_id=owner_id, name=name)
        # Стартовые предметы
        pet.add_item("meat", 2)
        pet.add_item("berry", 1)
        pet.save()
        return pet

    def _touch(self) -> None:
        self.last_interaction = datetime.now(timezone.utc).isoformat()

    def _strengthen(self, habit: str, amount: float) -> None:
        current = self.habits.get(habit, 0.0)
        self.habits[habit] = min(1.0, current + amount)

    def _response(self, variants: list[str]) -> str:
        return random.choice(variants)
