"""
Dragon Pet Discord Bot
Добрый дракон с седлом — полный мир: магазин, дружба, мини-игры, инвентарь.
"""

import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button
from dotenv import load_dotenv

from dragon import DragonPet, ITEMS, format_item
from dragon.items import shop_list

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN не найден в .env")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def bar(value: float, length: int = 10) -> str:
    filled = max(0, min(length, int(value / 100 * length)))
    return "█" * filled + "░" * (length - filled)


def make_status_embed(pet: DragonPet) -> discord.Embed:
    data = pet.status_embed_dict()
    embed = discord.Embed(
        title=f"{data['emoji']} {data['name']}  •  Ур. {data['level']}",
        description=(
            f"*{data['species']}*\n{data['desc']}\n\n"
            f"**Настроение:** {data['mood']} {pet.mood_emoji()}"
        ),
        color=0x9F1239,
    )
    xp_bar_len = 12
    xp_filled = int((data["xp"] / data["xp_needed"]) * xp_bar_len) if data["xp_needed"] else 0
    xp_bar = "█" * xp_filled + "░" * (xp_bar_len - xp_filled)

    embed.add_field(name="Прогресс", value=f"⭐ XP  {xp_bar}  {data['xp']}/{data['xp_needed']}", inline=False)
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
    embed.add_field(
        name="Ресурсы",
        value=f"🪙 Монеты: **{data['coins']}**\n🎒 Предметов: **{data['inventory_count']}**\n🤝 Друзей: **{data['friends_count']}**",
        inline=False,
    )
    next_evo = data.get("next_evolution")
    if next_evo:
        embed.add_field(name="Следующая эволюция", value=f"Ур. **{next_evo[0]}** → {next_evo[1]}", inline=False)
    embed.set_footer(text="Добрый дракон с седлом всегда рядом 🔥")
    return embed


def make_inventory_embed(pet: DragonPet) -> discord.Embed:
    embed = discord.Embed(title=f"🎒 Инвентарь — {pet.name}", description=pet.inventory_text(), color=0x9F1239)
    embed.add_field(name="Монеты", value=f"🪙 {pet.coins}")
    embed.set_footer(text="/use <item> • /sell <item>")
    return embed


def level_up_text(pet: DragonPet) -> str:
    evo_msg = pet._check_evolution()
    parts = [f"🎉 **Уровень {pet.level}!** +10 🪙"]
    if evo_msg:
        parts.append(evo_msg)
    return "\n".join(parts)


class DragonView(View):
    def __init__(self, owner_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Это не твой дракон! `/claim` 🐉", ephemeral=True)
            return False
        return True

    async def _action(self, interaction: discord.Interaction, action: str):
        pet = DragonPet.load(self.owner_id)
        if not pet:
            await interaction.response.send_message("Дракон не найден.", ephemeral=True)
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
        elif action == "play":
            reply, leveled = pet.play()
        elif action == "rings":
            reply, leveled, _ = pet.fly_rings()

        pet.save()
        content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
        await interaction.response.edit_message(content=content, embed=make_status_embed(pet), view=self)

        try:
            msg = await interaction.original_response()
            reacts = {"feed": "🍖", "pet": "🥰", "fly": "🔥", "search": "🔍",
                      "hunt": "🏹", "play": "⚽", "rings": "🌀"}
            if action in reacts:
                await msg.add_reaction(reacts[action])
            if leveled:
                await msg.add_reaction("⭐")
        except Exception:
            pass

    @button(label="Покормить", style=discord.ButtonStyle.success, emoji="🍖", row=0)
    async def b_feed(self, i: discord.Interaction, b: Button):
        await self._action(i, "feed")

    @button(label="Почесать", style=discord.ButtonStyle.primary, emoji="🥰", row=0)
    async def b_pet(self, i: discord.Interaction, b: Button):
        await self._action(i, "pet")

    @button(label="Полететь", style=discord.ButtonStyle.danger, emoji="🔥", row=0)
    async def b_fly(self, i: discord.Interaction, b: Button):
        await self._action(i, "fly")

    @button(label="Поиск", style=discord.ButtonStyle.secondary, emoji="🔍", row=1)
    async def b_search(self, i: discord.Interaction, b: Button):
        await self._action(i, "search")

    @button(label="Охота", style=discord.ButtonStyle.secondary, emoji="🏹", row=1)
    async def b_hunt(self, i: discord.Interaction, b: Button):
        await self._action(i, "hunt")

    @button(label="Играть", style=discord.ButtonStyle.secondary, emoji="⚽", row=1)
    async def b_play(self, i: discord.Interaction, b: Button):
        await self._action(i, "play")

    @button(label="Кольца", style=discord.ButtonStyle.secondary, emoji="🌀", row=2)
    async def b_rings(self, i: discord.Interaction, b: Button):
        await self._action(i, "rings")

    @button(label="Инвентарь", style=discord.ButtonStyle.secondary, emoji="🎒", row=2)
    async def b_inv(self, i: discord.Interaction, b: Button):
        pet = DragonPet.load(self.owner_id)
        await i.response.send_message(embed=make_inventory_embed(pet), ephemeral=True)


@bot.event
async def on_ready():
    print(f"🐉 Вошёл как {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Команд: {len(synced)}")
    except Exception as e:
        print(e)


@bot.tree.command(name="claim", description="Завести дракона")
@app_commands.describe(name="Имя дракона")
async def claim(interaction: discord.Interaction, name: str = "Гроктар"):
    if DragonPet.load(interaction.user.id):
        await interaction.response.send_message("У тебя уже есть дракон!", ephemeral=True)
        return
    pet = DragonPet.create(interaction.user.id, name)
    embed = make_status_embed(pet)
    embed.description += "\n\nВ инвентаре есть еда, а в кошельке — монеты 🪙"
    await interaction.response.send_message(
        content=f"🎉 {interaction.user.mention} заводит дракона!",
        embed=embed, view=DragonView(interaction.user.id)
    )


@bot.tree.command(name="status", description="Статус дракона")
async def status(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    await interaction.response.send_message(embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="feed", description="Покормить")
async def feed(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled = pet.feed()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="pet", description="Почесать")
async def pet_cmd(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled = pet.pet()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="fly", description="Полететь")
async def fly(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled = pet.fly()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="talk", description="Поговорить")
@app_commands.describe(message="Текст")
async def talk(interaction: discord.Interaction, message: str = "Привет"):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled = pet.talk(message)
    pet.save()
    content = f"**Ты:** {message}\n**{pet.name}:** {reply}"
    if leveled:
        content += "\n\n" + level_up_text(pet)
    await interaction.response.send_message(content)


@bot.tree.command(name="daily", description="Ежедневная награда")
async def daily(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    text, leveled, _ = pet.claim_daily()
    pet.save()
    content = text + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="inventory", description="Инвентарь")
async def inventory(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    await interaction.response.send_message(embed=make_inventory_embed(pet))


@bot.tree.command(name="use", description="Использовать предмет")
@app_commands.describe(item="ID предмета")
async def use_item_cmd(interaction: discord.Interaction, item: str):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled = pet.use_item(item.lower().strip())
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="shop", description="Магазин предметов")
async def shop(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    coins = pet.coins if pet else 0
    embed = discord.Embed(
        title="🏪 Магазин драконьих товаров",
        description=shop_list() + f"\n\nТвои монеты: **{coins}** 🪙",
        color=0x9F1239,
    )
    embed.set_footer(text="Купить: /buy <item> [количество]")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="buy", description="Купить предмет")
@app_commands.describe(item="ID предмета", amount="Количество")
async def buy(interaction: discord.Interaction, item: str, amount: int = 1):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    if amount < 1 or amount > 20:
        await interaction.response.send_message("Количество от 1 до 20.", ephemeral=True)
        return
    result = pet.buy_item(item.lower().strip(), amount)
    pet.save()
    await interaction.response.send_message(result)


@bot.tree.command(name="sell", description="Продать предмет")
@app_commands.describe(item="ID предмета", amount="Количество")
async def sell(interaction: discord.Interaction, item: str, amount: int = 1):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    result = pet.sell_item(item.lower().strip(), amount)
    pet.save()
    await interaction.response.send_message(result)


@bot.tree.command(name="gift", description="Подарить предмет другому дракону")
@app_commands.describe(user="Кому подарить", item="ID предмета")
async def gift(interaction: discord.Interaction, user: discord.Member, item: str):
    pet = DragonPet.load(interaction.user.id)
    target = DragonPet.load(user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    if not target:
        await interaction.response.send_message(f"У {user.display_name} ещё нет дракона.", ephemeral=True)
        return
    if user.id == interaction.user.id:
        await interaction.response.send_message("Нельзя дарить самому себе.", ephemeral=True)
        return
    result = pet.gift_item(target, item.lower().strip())
    pet.save()
    target.save()
    await interaction.response.send_message(result)


@bot.tree.command(name="friend", description="Добавить дракона в друзья")
@app_commands.describe(user="Чьего дракона добавить")
async def friend(interaction: discord.Interaction, user: discord.Member):
    pet = DragonPet.load(interaction.user.id)
    target = DragonPet.load(user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    if not target:
        await interaction.response.send_message(f"У {user.display_name} нет дракона.", ephemeral=True)
        return
    result = pet.add_friend(user.id)
    # Взаимно
    if str(interaction.user.id) not in target.friends:
        target.add_friend(interaction.user.id)
    pet.save()
    target.save()
    await interaction.response.send_message(result)


@bot.tree.command(name="friends", description="Список друзей дракона")
async def friends(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    embed = discord.Embed(title=f"🤝 Друзья — {pet.name}", description=pet.friends_text(), color=0x9F1239)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="search", description="Поиск камушков")
async def search(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled, _ = pet.search_stones()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="hunt", description="Охота")
async def hunt(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled, _ = pet.hunt()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="play", description="Поиграть с драконом")
async def play(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled = pet.play()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


@bot.tree.command(name="rings", description="Полёт сквозь кольца")
async def rings(interaction: discord.Interaction):
    pet = DragonPet.load(interaction.user.id)
    if not pet:
        await interaction.response.send_message("Сначала `/claim`", ephemeral=True)
        return
    reply, leveled, coins = pet.fly_rings()
    pet.save()
    content = reply + ("\n\n" + level_up_text(pet) if leveled else "")
    await interaction.response.send_message(content=content, embed=make_status_embed(pet), view=DragonView(interaction.user.id))


if __name__ == "__main__":
    bot.run(TOKEN)
