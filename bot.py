"""
Dragon Pet Discord Bot
Добрый дракон с седлом — твой виртуальный питомец.
Кнопки • Уровни • Инвентарь • Мини-игры • Эволюция
"""

import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button, Select
from dotenv import load_dotenv

from dragon import DragonPet, ITEMS, format_item

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN не найден в .env")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ====================== EMBEDS ======================

def bar(value: float, length: int = 10) -> str:
    filled = max(0, min(length, int(value / 100 * length)))
    return "█" * filled + "░" * (length - filled)


def make_status_embed(pet: DragonPet) -> discord.Embed:
    data = pet.status_embed_dict()
    emoji = data["emoji"]

    embed = discord.Embed(
        title=f"{emoji} {data['name']}  •  Ур. {data['level']}",
        description=(
            f"*{data['species']}*\n"
            f"{data['desc']}\n\n"
            f"**Настроение:** {data['mood']} {pet.mood_emoji()}"
        ),
        color=0x9F1239,
    )

    xp_bar_len = 12
    xp_filled = int((data["xp"] / data["xp_needed"]) * xp_bar_len) if data["xp_needed"] else 0
    xp_bar = "█" * xp_filled + "░" * (xp_bar_len - xp_filled)

    embed.add_field(
        name="Прогресс",
        value=f"⭐ XP  {xp_bar}  {data['xp']}/{data['xp_needed']}",
        inline=False,
    )

    embed.add_field(
        name="Статы",
        value=(
            f"🍖 Голод          {bar(data['hunger'])} {data['hunger']}%\n"
            f"💖 Счастье        {bar(data['happiness'])} {data['happiness']}%\n"
            f"⚡ Энергия        {bar(data['energy'])} {data['energy']}%\n"
            f"🥰 Привязанность  {bar(data['affection'])} {data['affection']}%"
        ),
        inline=False,
    )

    inv_count = data.get("inventory_count", 0)
    embed.add_field(
        name="Инвентарь",
        value=f"🎒 Предметов: **{inv_count}**  (смотри `/inventory`)",
        inline=False,
    )

    habits = data["habits"]
    if habits:
        habits_text = "\n".join(
            f"• {name} ({int(strength * 100)}%)"
            for name, strength in list(habits.items())[:4]
        )
        embed.add_field(name="Сильные привычки", value=habits_text, inline=False)

    next_evo = data.get("next_evolution")
    if next_evo:
        req_level, next_name = next_evo
        embed.add_field(
            name="Следующая эволюция",
            value=f"Уровень **{req_level}** → {next_name}",
            inline=False,
        )
    else:
        embed.add_field(name="Эволюция", value="✨ Максимальная форма достигнута!", inline=False)

    embed.set_footer(text="Добрый дракон с седлом всегда рядом 🔥 • Кнопки ниже")
    return embed


def make_inventory_embed(pet: DragonPet) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎒 Инвентарь — {pet.name}",
        color=0x9F1239,
    )
    text = pet.inventory_text()
    embed.description = text
    embed.set_footer(text="Используй /use <предмет> чтобы применить")
    return embed


def level_up_text(pet: DragonPet) -> str:
    evo_msg = pet._check_evolution()
    parts = [f"🎉 **Уровень {pet.level}!** {pet.name} стал сильнее!"]
    if evo_msg:
        parts.append(evo_msg)
    return "\n".join(parts)


# ====================== КНОПКИ ======================

class DragonView(View):
    def __init__(self, owner_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Это не твой дракон! Заведи своего через `/claim` 🐉",
                ephemeral=True,
            )
            return False
        return True

    async def _do_action(self, interaction: discord.Interaction, action: str):
        pet = DragonPet.load(self.owner_id)
        if not pet:
            await interaction.response.send_message("Дракон исчез… Используй `/claim`", ephemeral=True)
            return

        leveled = False
        reply = ""

        if action == "feed":
            reply, leveled = pet.feed()
        elif action == "pet":
            reply, leveled = pet.pet()
        elif action == "fly":
            reply, leveled = pet.fly()
        elif action == "search":
            reply, leveled, _ = pet.search_stones()
        elif action == "hunt":
            reply, leveled, _ = pet.hunt()
        else:
            reply = "Неизвестное действие"

        pet.save()

        content = reply
        if leveled:
            content += "\n\n" + level_up_text(pet)

        embed = make_status_embed(pet)
        await interaction.response.edit_message(content=content, embed=embed, view=self)

        try:
            msg = await interaction.original_response()
            reactions = {
                "feed": "🍖", "pet": "🥰", "fly": "🔥",
                "search": "🔍", "hunt": "🏹",
            }
            if action in reactions:
                await msg.add_reaction(reactions[action])
            if leveled:
                await msg.add_reaction("⭐")
                await msg.add_reaction("✨")
        except Exception:
            pass

    @button(label="Покормить", style=discord.ButtonStyle.success, emoji="🍖", row=0)
    async def feed_button(self, interaction: discord.Interaction, button: Button):
        await self._do_action(interaction, "feed")

    @button(label="Почесать", style=discord.ButtonStyle.primary, emoji="🥰", row=0)
    async def pet_button(self, interaction: discord.Interaction, button: Button):
        await self._do_action(interaction, "pet")

    @button(label="Полететь", style=discord.ButtonStyle.danger, emoji="🔥", row=0)
    async def fly_button(self, interaction: discord.Interaction, button: Button):
        await self._do_action(interaction, "fly")

    @button(label="Поиск камушков", style=discord.ButtonStyle.secondary, emoji="🔍", row=1)
    async def search_button(self, interaction: discord.Interaction, button: Button):
        await self._do_action(interaction, "search")

    @button(label="Охота", style=discord.ButtonStyle.secondary, emoji="🏹", row=1)
    async def hunt_button(self, interaction: discord.Interaction, button: Button):
        await self._do_action(interaction, "hunt")

    @button(label="Инвентарь", style=discord.ButtonStyle.secondary, emoji="🎒", row=1)
    async def inv_button(self, interaction: discord.Interaction, button: Button):
        pet = DragonPet.load(self.owner_id)
        if not pet:
            await interaction.response.send_message("Дракон не найден.", ephemeral=True)
            return
        await interaction.response.send_message(embed=make_inventory_embed(pet), ephemeral=True)


# ====================== КОМАНДЫ ======================

@bot.event
async def on_ready():
    print(f"🐉 Вошёл как {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано команд: {len(synced)}")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")


@bot.tree.command(name="claim", description="Завести своего доброго дракона с седлом")
@app_commands.describe(name="Имя дракона (по умолчанию Гроктар)")
async def claim(interaction: discord.Interaction, name: str = "Гроктар"):
    existing = DragonPet.load(interaction.user.id)
    if existing:
        await interaction.response.send_message(
            f"У тебя уже есть дракон **{existing.name}**! Используй `/status`.",
            ephemeral=True,
        )
        return

    pet = DragonPet.create(interaction.user.id, name)
    embed = make_status_embed(pet)
    embed.description = (
        f"*{pet.species}*\n\n"
        f"**{pet.name}** теперь твой!\n"
        f"Он уже проверяет седло и ждёт, когда ты сядешь.\n"
        f"В инвентаре уже есть немного еды 🍖"
    )
    view = DragonView(interaction.user.id)
    await interaction.response.send_message(
        content=f"🎉 {interaction.user.mention} заводит дракона!",
        embed=embed,
        view=view,
    )
    try:
        msg = await interaction.original_response()
        await msg.add_reaction("🐉")
        await msg.add_reaction("✨")
    except Exception:
        pass


@bot.tree.command(name="status", description="Посмотреть состояние своего дракона")
async def status(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("У тебя ещё нет дракона. Используй `/claim`!", ephemeral=True)
        return
    view = DragonView(interaction.user.id)
    await interaction.response.send_message(embed=make_status_embed(pet), view=view)


@bot.tree.command(name="feed", description="Покормить дракона")
async def feed(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return
    reply, leveled = pet.feed()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    view = DragonView(interaction.user.id)
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=view)


@bot.tree.command(name="pet", description="Почесать дракона за ушком")
async def pet_cmd(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return
    reply, leveled = pet.pet()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    view = DragonView(interaction.user.id)
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=view)


@bot.tree.command(name="fly", description="Сесть в седло и полетать")
async def fly(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return
    reply, leveled = pet.fly()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    view = DragonView(interaction.user.id)
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=view)


@bot.tree.command(name="talk", description="Поговорить с драконом")
@app_commands.describe(message="Что сказать дракону")
async def talk(interaction: discord.Interaction, message: str = "Привет"):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return
    reply, leveled = pet.talk(message)
    pet.save()
    content = f"**Ты:** {message}\n**{pet.name}:** {reply}"
    if leveled:
        content += "\n\n" + level_up_text(pet)
    await interaction.response.send_message(content)


@bot.tree.command(name="daily", description="Получить ежедневную награду")
async def daily(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return
    text, leveled, _ = pet.claim_daily()
    pet.save()
    content = text + ("\n\n" + level_up_text(pet) if leveled else "")
    view = DragonView(interaction.user.id)
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=view)


@bot.tree.command(name="inventory", description="Посмотреть инвентарь дракона")
async def inventory(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return
    await interaction.response.send_message(embed=make_inventory_embed(pet))


@bot.tree.command(name="use", description="Использовать / подарить предмет из инвентаря")
@app_commands.describe(item="ID предмета (meat, fish, berry, shiny_stone, saddle_oil...)")
async def use_item(interaction: discord.Interaction, item: str):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return

    item = item.lower().strip()
    reply, leveled = pet.use_item(item)
    pet.save()

    content = reply
    if leveled:
        content += "\n\n" + level_up_text(pet)

    view = DragonView(interaction.user.id)
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=view)


@bot.tree.command(name="search", description="Мини-игра: поиск блестящих камушков")
async def search(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return

    reply, leveled, found = pet.search_stones()
    pet.save()

    content = reply
    if leveled:
        content += "\n\n" + level_up_text(pet)

    view = DragonView(interaction.user.id)
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=view)

    try:
        msg = await interaction.original_response()
        await msg.add_reaction("🔍")
        if found:
            await msg.add_reaction("💎")
        if leveled:
            await msg.add_reaction("⭐")
    except Exception:
        pass


@bot.tree.command(name="hunt", description="Мини-игра: охота за едой и ресурсами")
async def hunt(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return

    reply, leveled, found = pet.hunt()
    pet.save()

    content = reply
    if leveled:
        content += "\n\n" + level_up_text(pet)

    view = DragonView(interaction.user.id)
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=view)

    try:
        msg = await interaction.original_response()
        await msg.add_reaction("🏹")
        if found:
            await msg.add_reaction("🍖")
        if leveled:
            await msg.add_reaction("⭐")
    except Exception:
        pass


if __name__ == "__main__":
    bot.run(TOKEN)
