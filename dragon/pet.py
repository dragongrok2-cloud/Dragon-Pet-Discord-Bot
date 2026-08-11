"""Ядро Dragon Pet: уровни, эволюция, инвентарь, магазин, дружба и мини-игры."""

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

    coins: int = 50  # валюта магазина

    habits: Dict[str, float] = field(default_factory=lambda: {
        "всегда проверяет седло": 0.75,
        "любит почесывания за ухом": 0.70,
        "рычит от удовольствия": 0.55,
        "греет всадника крылом": 0.50,
        "собирает блестящие камушки": 0.30,
    })

    inventory: Dict[str, int] = field(default_factory=dict)

    # Дружба: owner_id (str) → уровень дружбы (0–100)
    friends: Dict[str, int] = field(default_factory=dict)

    last_interaction: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_daily: str = ""
    last_search: str = ""
    last_hunt: str = ""
    last_play: str = ""
    last_rings: str = ""
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
        coins_reward = 20 + self.level * 3

        self.hunger = max(0.0, self.hunger - hunger_restore)
        self.happiness = min(100.0, self.happiness + happiness_boost)
        self.energy = min(100.0, self.energy + energy_boost)
        self.affection = min(100.0, self.affection + 5)
        self.coins += coins_reward

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
            f"🎁 **Ежедневная награда!**\n"
            f"• −{hunger_restore} голода • +{happiness_boost} счастья • +{energy_boost} энергии\n"
            f"• +{xp_reward} XP • +{coins_reward} 🪙"
        )
        if daily_items:
            text += "\n• Предметы: " + ", ".join(format_item(i, 1) for i in daily_items)
        return text, leveled, {"xp": xp_reward, "coins": coins_reward}

    # ---------- инвентарь и магазин ----------

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

        if item_id == "shiny_stone":
            self._strengthen("собирает блестящие камушки", 0.12)
            text = f"*глаза вспыхивают* Ооо… блестящий! Спасибо! {item['emoji']}"
        elif item_id in ("meat", "fish", "berry"):
            text = f"*довольно ест* Ммм, {item['name']}! 🔥"
        elif item_id == "saddle_oil":
            text = f"*довольно фыркает* Седло теперь ещё удобнее!"
        elif item_id == "play_ball":
            text = f"*радостно подбрасывает мяч* Давай играть! ⚽"
        else:
            text = f"Ты используешь {item['emoji']} **{item['name']}**. Эффект применён!"
        return text, leveled

    def buy_item(self, item_id: str, count: int = 1) -> str:
        item = get_item(item_id)
        if not item:
            return "Такого предмета нет в магазине."
        price = item.get("buy_price", 0)
        if price <= 0:
            return f"{item['emoji']} {item['name']} нельзя купить."
        total = price * count
        if self.coins < total:
            return f"Не хватает монет. Нужно {total} 🪙, у тебя {self.coins} 🪙."
        self.coins -= total
        self.add_item(item_id, count)
        self._touch()
        return f"✅ Куплено {format_item(item_id, count)} за {total} 🪙\nОсталось: {self.coins} 🪙"

    def sell_item(self, item_id: str, count: int = 1) -> str:
        item = get_item(item_id)
        if not item:
            return "Такого предмета не существует."
        if not self.remove_item(item_id, count):
            return f"У тебя нет столько {item['emoji']} {item['name']}."
        price = item.get("sell_price", 0) * count
        self.coins += price
        self._touch()
        return f"✅ Продано {format_item(item_id, count)} за {price} 🪙\nТеперь у тебя: {self.coins} 🪙"

    def gift_item(self, target: "DragonPet", item_id: str) -> str:
        item = get_item(item_id)
        if not item:
            return "Такого предмета нет."
        if not self.remove_item(item_id, 1):
            return f"У тебя нет {item['emoji']} {item['name']}."
        target.add_item(item_id, 1)
        # Укрепляем дружбу
        tid = str(target.owner_id)
        self.friends[tid] = min(100, self.friends.get(tid, 0) + 8)
        target.friends[str(self.owner_id)] = min(100, target.friends.get(str(self.owner_id), 0) + 8)
        self.happiness = min(100.0, self.happiness + 5)
        target.happiness = min(100.0, target.happiness + 10)
        self._touch()
        target._touch()
        return (
            f"🎁 Ты подарил {format_item(item_id)} дракону **{target.name}**!\n"
            f"Дружба между вами окрепла."
        )

    def inventory_text(self) -> str:
        if not self.inventory:
            return "Инвентарь пуст."
        lines = [format_item(iid, cnt) for iid, cnt in sorted(self.inventory.items())]
        return "\n".join(lines)

    # ---------- дружба ----------

    def add_friend(self, other_id: int) -> str:
        oid = str(other_id)
        if oid == str(self.owner_id):
            return "Нельзя добавить самого себя."
        if oid in self.friends:
            return "Этот дракон уже у тебя в друзьях."
        self.friends[oid] = 10
        self._touch()
        return f"🤝 Дракон добавлен в друзья! Начальный уровень дружбы: 10"

    def friendship_level(self, other_id: int) -> int:
        return self.friends.get(str(other_id), 0)

    def friends_text(self) -> str:
        if not self.friends:
            return "Пока нет друзей. Добавь кого-нибудь через `/friend @user`!"
        lines = []
        for oid, lvl in sorted(self.friends.items(), key=lambda x: -x[1]):
            lines.append(f"• <@{oid}> — дружба {lvl}/100")
        return "\n".join(lines)

    # ---------- мини-игры ----------

    def can_search(self) -> Tuple[bool, str]:
        if self.energy < 15:
            return False, "Мало энергии для поиска."
        if self.last_search:
            last = datetime.fromisoformat(self.last_search)
            if (datetime.now(timezone.utc) - last).total_seconds() < 300:
                left = int(300 - (datetime.now(timezone.utc) - last).total_seconds())
                return False, f"Поиск на перезарядке ({left} сек)."
        return True, ""

    def search_stones(self) -> Tuple[str, bool, List[str]]:
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
            self.add_item("dragon_scale", 1); found.append("dragon_scale")
        if roll < 0.25:
            self.add_item("shiny_stone", random.randint(1, 2)); found.append("shiny_stone")
        if roll < 0.45:
            self.add_item("ancient_coin", 1); found.append("ancient_coin")
            self.coins += 8
        if roll < 0.70:
            self.add_item("berry", 1); found.append("berry")
        if not found and random.random() < 0.5:
            self.add_item("shiny_stone", 1); found.append("shiny_stone")

        leveled = self._add_xp(10 + len(found) * 5)
        if found:
            text = f"🔍 *рыщет*\nНашёл: {', '.join(format_item(i) for i in found)}!"
        else:
            text = "🔍 *долго ищет* В этот раз пусто…"
        return text, leveled, found

    def can_hunt(self) -> Tuple[bool, str]:
        if self.energy < 25:
            return False, "Мало энергии для охоты."
        if self.hunger > 85:
            return False, "Слишком голоден."
        if self.last_hunt:
            last = datetime.fromisoformat(self.last_hunt)
            if (datetime.now(timezone.utc) - last).total_seconds() < 600:
                left = int(600 - (datetime.now(timezone.utc) - last).total_seconds())
                return False, f"Охота на перезарядке ({left} сек)."
        return True, ""

    def hunt(self) -> Tuple[str, bool, List[str]]:
        ok, msg = self.can_hunt()
        if not ok:
            return msg, False, []
        self.last_hunt = datetime.now(timezone.utc).isoformat()
        self.energy = max(0.0, self.energy - 22)
        self.hunger = min(100.0, self.hunger + 12)
        self._touch()

        found = []
        success = random.random() < (0.55 + self.level * 0.01 + self.happiness / 500)
        if success:
            roll = random.random()
            if roll < 0.15: self.add_item("meat", random.randint(1, 2)); found.append("meat")
            if roll < 0.40: self.add_item("fish", random.randint(1, 2)); found.append("fish")
            if roll < 0.55: self.add_item("cloud_essence", 1); found.append("cloud_essence")
            if roll < 0.70: self.add_item("saddle_oil", 1); found.append("saddle_oil")
            if not found: self.add_item("meat", 1); found.append("meat")
            self.coins += random.randint(5, 15)
            leveled = self._add_xp(18 + len(found) * 6)
            text = f"🏹 *точный удар*\nДобыча: {', '.join(format_item(i) for i in found)}"
        else:
            leveled = self._add_xp(6)
            text = "🏹 *промах* Добыча ускользнула…"
        return text, leveled, found

    def can_play(self) -> Tuple[bool, str]:
        if self.energy < 10:
            return False, "Слишком устал для игр."
        if self.last_play:
            last = datetime.fromisoformat(self.last_play)
            if (datetime.now(timezone.utc) - last).total_seconds() < 180:
                left = int(180 - (datetime.now(timezone.utc) - last).total_seconds())
                return False, f"Играть можно через {left} сек."
        return True, ""

    def play(self) -> Tuple[str, bool]:
        """Мини-игра: весёлая игра."""
        ok, msg = self.can_play()
        if not ok:
            return msg, False
        self.last_play = datetime.now(timezone.utc).isoformat()
        self.energy = max(0.0, self.energy - 10)
        self.happiness = min(100.0, self.happiness + 18)
        self.affection = min(100.0, self.affection + 6)
        self._touch()
        self._strengthen("рычит от удовольствия", 0.06)
        leveled = self._add_xp(14)
        text = self._response([
            "*радостно крутится и подпрыгивает* Это было весело! ⚽",
            "*играючи кусает воздух* Ещё! Ещё!",
            "*довольно фыркает* Ты лучший напарник для игр.",
        ])
        return text, leveled

    def can_rings(self) -> Tuple[bool, str]:
        if self.energy < 20:
            return False, "Мало энергии для полёта сквозь кольца."
        if self.last_rings:
            last = datetime.fromisoformat(self.last_rings)
            if (datetime.now(timezone.utc) - last).total_seconds() < 420:
                left = int(420 - (datetime.now(timezone.utc) - last).total_seconds())
                return False, f"Испытание колец на перезарядке ({left} сек)."
        return True, ""

    def fly_rings(self) -> Tuple[str, bool, int]:
        """Мини-игра: полёт сквозь кольца. Возвращает (текст, level_up, монеты)."""
        ok, msg = self.can_rings()
        if not ok:
            return msg, False, 0
        self.last_rings = datetime.now(timezone.utc).isoformat()
        self.energy = max(0.0, self.energy - 18)
        self.hunger = min(100.0, self.hunger + 8)
        self._touch()
        self._strengthen("всегда проверяет седло", 0.05)

        # Успех зависит от уровня и энергии
        score = random.randint(3, 10) + min(5, self.level // 3)
        coins_won = score * 3
        xp_won = 12 + score * 2

        self.coins += coins_won
        self.happiness = min(100.0, self.happiness + score)
        leveled = self._add_xp(xp_won)

        if score >= 12:
            text = f"🌀 *пролетает все кольца идеально!*\nНевероятный полёт! +{coins_won} 🪙 и куча опыта!"
        elif score >= 8:
            text = f"🌀 *ловко проходит большинство колец*\nОтличный результат! +{coins_won} 🪙"
        else:
            text = f"🌀 *проходит несколько колец*\nНеплохо для начала. +{coins_won} 🪙"
        return text, leveled, coins_won

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
            self.coins += 10
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
            "coins": self.coins,
            "mood": self.mood_text(),
            "habits": self.strong_habits(),
            "next_evolution": next_evo,
            "inventory_count": sum(self.inventory.values()),
            "friends_count": len(self.friends),
            "last_interaction": self.last_interaction,
        }

    def mood_text(self) -> str:
        if self.happiness >= 85: return "Счастлив и полон сил"
        if self.happiness >= 65: return "Доволен"
        if self.happiness >= 40: return "Нормально"
        if self.hunger > 75: return "Голоден и немного грустен"
        return "Устал или скучает"

    def mood_emoji(self) -> str:
        if self.happiness >= 80: return "🥰"
        if self.happiness >= 60: return "😊"
        if self.hunger > 70: return "🥺"
        if self.energy < 30: return "😴"
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
        defaults = {
            "level": 1, "xp": 0, "evolution_stage": 0, "last_daily": "",
            "inventory": {}, "last_search": "", "last_hunt": "",
            "coins": 50, "friends": {}, "last_play": "", "last_rings": "",
        }
        for k, v in defaults.items():
            data.setdefault(k, v)
        return cls(**data)

    @classmethod
    def create(cls, owner_id: int, name: str = "Гроктар") -> "DragonPet":
        pet = cls(owner_id=owner_id, name=name)
        pet.add_item("meat", 2)
        pet.add_item("berry", 1)
        pet.coins = 80
        pet.save()
        return pet

    def _touch(self) -> None:
        self.last_interaction = datetime.now(timezone.utc).isoformat()

    def _strengthen(self, habit: str, amount: float) -> None:
        self.habits[habit] = min(1.0, self.habits.get(habit, 0.0) + amount)

    def _response(self, variants: list[str]) -> str:
        return random.choice(variants)
