"""Ядро виртуального дракона-питомца."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Optional
import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass
class DragonPet:
    """Добрый дракон с седлом — твой личный питомец."""

    owner_id: int
    name: str = "Гроктар"
    species: str = "Добрый огненный дракон с седлом"

    # Основные статы (0–100)
    hunger: float = 40.0          # 0 = сыт, 100 = очень голоден
    happiness: float = 70.0
    energy: float = 80.0
    affection: float = 50.0       # привязанность к хозяину

    # Привычки: название → сила 0.0–1.0
    habits: Dict[str, float] = field(default_factory=lambda: {
        "всегда проверяет седло": 0.75,
        "любит почесывания за ухом": 0.70,
        "рычит от удовольствия": 0.55,
        "греет всадника крылом": 0.50,
        "собирает блестящие камушки": 0.30,
    })

    last_interaction: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ---------- действия ----------

    def feed(self, amount: float = 25.0) -> str:
        self.hunger = max(0.0, self.hunger - amount)
        self.happiness = min(100.0, self.happiness + 8)
        self.energy = min(100.0, self.energy + 5)
        self._touch()
        self._strengthen("собирает блестящие камушки", 0.02)
        return self._response([
            f"*довольно урчит и жадно ест* Ммм… вкусно! Спасибо, всадник.",
            f"*осторожно берёт угощение когтями* Теперь я сытее и готов к приключениям.",
            f"*огненный язык мелькает* Отличный обед! Седло уже ждет.",
        ])

    def pet(self) -> str:
        self.happiness = min(100.0, self.happiness + 15)
        self.affection = min(100.0, self.affection + 10)
        self.energy = min(100.0, self.energy + 3)
        self._touch()
        self._strengthen("любит почесывания за ухом", 0.08)
        self._strengthen("рычит от удовольствия", 0.05)
        return self._response([
            f"*прищуривается и тихо рычит от удовольствия* Мрррр… ещё чуть-чуть за ушком…",
            f"*опускает огромную голову к тебе* Вот здесь… да… идеально.",
            f"*крылья слегка подрагивают* Ты лучший всадник на свете.",
        ])

    def fly(self) -> str:
        if self.energy < 20:
            return "*устало опускает крылья* Я слишком устал… дай мне отдохнуть или покорми."
        if self.hunger > 80:
            return "*жалобно смотрит* Сначала покорми меня, а то силы закончатся в воздухе…"

        self.energy = max(0.0, self.energy - 20)
        self.happiness = min(100.0, self.happiness + 12)
        self.affection = min(100.0, self.affection + 5)
        self.hunger = min(100.0, self.hunger + 10)
        self._touch()
        self._strengthen("всегда проверяет седло", 0.06)
        self._strengthen("греет всадника крылом", 0.04)

        return self._response([
            f"*проверяет ремни седла и мощно взмахивает крыльями* Держись крепче! Мы взлетаем! 🔥",
            f"*поднимается в небо* Ветер в морде, солнце на чешуе… Это жизнь, всадник!",
            f"*делает плавный вираж* Смотри, какие облака! Хочешь повыше?",
        ])

    def talk(self, text: str = "") -> str:
        self.happiness = min(100.0, self.happiness + 4)
        self.affection = min(100.0, self.affection + 3)
        self._touch()

        mood = self.mood_emoji()
        if self.happiness > 80:
            return f"{mood} *радостно фыркает* Я так рад тебя слышать! Расскажи ещё…"
        if self.hunger > 70:
            return f"{mood} *тихонько урчит* Я бы с удовольствием поговорил… после еды."
        if self.energy < 30:
            return f"{mood} *зевает огромной пастью* Давай чуть позже, я немного сонный…"
        return f"{mood} *внимательно слушает, наклонив голову* Я здесь. Говори, что на душе."

    # ---------- состояние ----------

    def status_embed_dict(self) -> dict:
        """Данные для красивого embed."""
        return {
            "name": self.name,
            "species": self.species,
            "hunger": round(self.hunger),
            "happiness": round(self.happiness),
            "energy": round(self.energy),
            "affection": round(self.affection),
            "mood": self.mood_text(),
            "habits": self.strong_habits(),
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
        import random
        return random.choice(variants)
