"""
Dragon Pet Discord Bot
Добрый дракон с седлом — твой виртуальный питомец.
"""

import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from dragon import DragonPet

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN не найден в .env")

intents = discord.Intents.default()
intents.message_content = True  # если понадобится обычные сообщения

bot = commands.Bot(command_prefix="!", intents=intents)


def get_or_create_pet(user_id: int, name: str | None = None) -> DragonPet:
    pet = DragonPet.load(user_id)
    if pet is None:
        pet = DragonPet.create(user_id, name or "Гроктар")
    return pet


def make_status_embed(pet: DragonPet) -> discord.Embed:
    data = pet.status_embed_dict()

    def bar(value: float, length: int = 10) -> str:
        filled = int(value / 100 * length)
        return "█" * filled + "░" * (length - filled)

    embed = discord.Embed(
        title=f"🐉 {data['name']}",
        description=f"*{data['species']}*\n\n**Настроение:** {data['mood']} {pet.mood_emoji()}",
        color=0x9F1239,  # драконий тёмно-красный
    )

    embed.add_field(
        name="Статы",
        value=(
            f"🍖 Голод     {bar(data['hunger'])} {data['hunger']}%\n"
            f"💖 Счастье   {bar(data['happiness'])} {data['happiness']}%\n"
            f"⚡ Энергия   {bar(data['energy'])} {data['energy']}%\n"
            f"🥰 Привязанность {bar(data['affection'])} {data['affection']}%"
        ),
        inline=False,
    )

    habits = data["habits"]
    if habits:
        habits_text = "\n".join(
            f"• {name} ({int(strength*100)}%)"
            for name, strength in list(habits.items())[:5]
        )
        embed.add_field(name="Сильные привычки", value=habits_text, inline=False)

    embed.set_footer(text="Добрый дракон с седлом всегда рядом 🔥")
    return embed


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
        f"Он уже проверяет седло и ждёт, когда ты сядешь."
    )
    await interaction.response.send_message(
        content=f"🎉 {interaction.user.mention} заводит дракона!",
        embed=embed,
    )


@bot.tree.command(name="status", description="Посмотреть состояние своего дракона")
async def status(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message(
            "У тебя ещё нет дракона. Используй `/claim`!",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(embed=make_status_embed(pet))


@bot.tree.command(name="feed", description="Покормить дракона")
async def feed(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return

    reply = pet.feed()
    pet.save()
    await interaction.response.send_message(f"{reply}\n\n", embed=make_status_embed(pet))


@bot.tree.command(name="pet", description="Почесать дракона за ушком")
async def pet_cmd(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return

    reply = pet.pet()
    pet.save()
    await interaction.response.send_message(f"{reply}\n\n", embed=make_status_embed(pet))


@bot.tree.command(name="fly", description="Сесть в седло и полетать")
async def fly(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return

    reply = pet.fly()
    pet.save()
    await interaction.response.send_message(f"{reply}\n\n", embed=make_status_embed(pet))


@bot.tree.command(name="talk", description="Поговорить с драконом")
@app_commands.describe(message="Что сказать дракону")
async def talk(interaction: discord.Interaction, message: str = "Привет"):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала заведи дракона: `/claim`", ephemeral=True)
        return

    reply = pet.talk(message)
    pet.save()
    await interaction.response.send_message(f"**Ты:** {message}\n**{pet.name}:** {reply}")


if __name__ == "__main__":
    bot.run(TOKEN)
