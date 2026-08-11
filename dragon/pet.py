"""Ядро виртуального дракона-питомца с уровнями, эволюцией и ежедневными наградами."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
import json
import random
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Стадии эволюции: (мин. уровень, название вида, эмодзи, описание)
EVOLUTION_STAGES = [
    (1,  "Маленький дракончик с седлом",          "🐣", "Только-только вылупился, но уже проверяет седло."),
    (5,  "Молодой огненный дракон с седлом",      "🐉", "Крылья крепнут, характер проявляется."),
    (12, "Добрый огненный дракон с седлом",       "🔥🐉", "Настоящий компаньон. Седло сидит идеально."),
    (20, "Древний страж с пылающим седлом",       "✨🐉", "Мудрость веков и огонь, который греет душу."),
    (35, "Легендарный Небесный Дракон",           "🌌🐉", "Легенда, которая летает между звёздами."),
]


def xp_for_level(level: int) -> int:
    """Сколько XP нужно для перехода с текущего уровня на следующий."""
    return 50 + (level - 1) * 25


@dataclass
class DragonPet:
    """Добрый дракон с седлом — твой личный питомец."""

    owner_id: int
    name: str = "Гроктар"
    species: str = "Маленький дракончик с седлом"

    # Основные статы (0–100)
    hunger: float = 40.0
    happiness: float = 70.0
    energy: float = 80.0
    affection: float = 50.0

    # Прогрессия
    level: int = 1
    xp: int = 0
    evolution_stage: int = 0  # индекс в EVOLUTION_STAGES

    # Привычки: название → сила 0.0–1.0
    habits: Dict[str, float] = field(default_factory=lambda: {
        "всегда проверяет седло": 0.75,
        "любит почесывания за ухом": 0.70,
        "рычит от удовольствия": 0.55,
        "греет всадника крылом": 0.50,
        "собирает блестящие камушки": 0.30,
    })

    last_interaction: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_daily: str = ""  # ISO дата последнего /daily
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ---------- действия ----------

    def feed(self, amount: float = 25.0) -> Tuple[str, bool]:
        """Кормит. Возвращает (ответ, level_up?)."""
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
        """Ежедневная награда. Возвращает (текст, level_up?, бонусы)."""
        now = datetime.now(timezone.utc)
        if self.last_daily:
            last = datetime.fromisoformat(self.last_daily)
            if now.date() <= last.date():
                return "Ты уже получал ежедневную награду сегодня. Возвращайся завтра! 🌙", False, {}

        self.last_daily = now.isoformat()

        # Награды зависят от уровня
        hunger_restore = 30 + self.level * 2
        happiness_boost = 15 + self.level
        energy_boost = 20 + self.level
        xp_reward = 40 + self.level * 8

        self.hunger = max(0.0, self.hunger - hunger_restore)
        self.happiness = min(100.0, self.happiness + happiness_boost)
        self.energy = min(100.0, self.energy + energy_boost)
        self.affection = min(100.0, self.affection + 5)

        leveled = self._add_xp(xp_reward)
        self._touch()

        # Шанс получить новую привычку или усилить
        if random.random() < 0.35:
            new_habits = [
                "любит смотреть на закаты",
                "всегда ждёт у окна",
                "собирает блестящие камушки",
                "греет всадника крылом",
                "рычит колыбельные",
            ]
            habit = random.choice(new_habits)
            self._strengthen(habit, 0.15)

        bonuses = {
            "hunger": hunger_restore,
            "happiness": happiness_boost,
            "energy": energy_boost,
            "xp": xp_reward,
        }

        text = (
            f"🎁 **Ежедневная награда получена!**\n"
            f"• −{hunger_restore} голода\n"
            f"• +{happiness_boost} счастья\n"
            f"• +{energy_boost} энергии\n"
            f"• +{xp_reward} опыта"
        )
        return text, leveled, bonuses

    # ---------- прогрессия ----------

    def _add_xp(self, amount: int) -> bool:
        """Добавляет XP. Возвращает True если был level-up."""
        self.xp += amount
        leveled = False

        while self.xp >= xp_for_level(self.level):
            self.xp -= xp_for_level(self.level)
            self.level += 1
            leveled = True
            # Небольшой бонус статов при уровне
            self.happiness = min(100.0, self.happiness + 5)
            self.affection = min(100.0, self.affection + 3)

            # Проверяем эволюцию
            self._check_evolution()

        return leveled

    def _check_evolution(self) -> Optional[str]:
        """Проверяет, можно ли эволюционировать. Возвращает сообщение если да."""
        for idx, (req_level, species, emoji, desc) in enumerate(EVOLUTION_STAGES):
            if self.level >= req_level and idx > self.evolution_stage:
                self.evolution_stage = idx
                self.species = species
                return f"{emoji} **ЭВОЛЮЦИЯ!** Теперь ты — **{species}**!\n*{desc}*"
        return None

    def evolution_info(self) -> Tuple[str, str, str]:
        """Текущая стадия: (emoji, species, description)"""
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
        # Совместимость со старыми сохранениями
        data.setdefault("level", 1)
        data.setdefault("xp", 0)
        data.setdefault("evolution_stage", 0)
        data.setdefault("last_daily", "")
        return cls(**data)

    @classmethod
    def create(cls, owner_id: int, name: str = "Гроктар") -> "DragonPet":
        pet = cls(owner_id=owner_id, name=name)
        pet.save()
        return pet

    # ---------- внутреннее ----------

    def _touch(self) -> None:
        self.last_interaction = datetime.now(timezone.utc).isoformat()

    def _strengthen(self, habit: str, amount: float) -> None:
        current = self.habits.get(habit, 0.0)
        self.habits[habit] = min(1.0, current + amount)

    def _response(self, variants: list[str]) -> str:
        return random.choice(variants)
