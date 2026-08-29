import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
import asyncio
import datetime
import json
import os
import aiosqlite
import openai
import random
import time
import math
from dotenv import load_dotenv
from openai import AsyncOpenAI

pending_invites = {}
pending_actions = {}

LOG_CHANNEL_ID = 1514982915921150083
MUTE_ROLE_ID = 1514982507014131828
ROLE_LOOT_STASH_LIMIT_ID = 1516895512207298680
ROLE_CUSTOM_ID           = 1507844200211681332
ROLE_SUMMER_LIMIT_ID     = 1515130377394458644
ROLE_ZERO_TWO_WIFE_ID = 1520899872243449947

load_dotenv()


GUILD_ID = 1488295467619061922

BUSINESS_LEVELS = {
    1: {"cost": 100000, "profit": 500},
    2: {"cost": 250000, "profit": 750},
    3: {"cost": 750000, "profit": 1000}
}

BUSINESS_PRICES = {
    1: 100000,
    2: 250000,
    3: 750000
}

PROFIT_PER_HOUR = {
    1: 5000,
    2: 15000,
    3: 50000
}

class Client(commands.Bot):
    async def on_message(self, message):
        if message.author == self.user:
            return
            
        if message.content.startswith('hello'):
            await message.channel.send(f'Hi there {message.author}')


    async def on_reaction_add(self, reaction, user):
        await reaction.message.channel.send('Да')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)

from discord.ext import tasks

@tasks.loop(hours=24)
async def payout_loop():
    print("Выплата запущена!")


GUILD_ID = discord.Object(id=1488295467619061922)




@client.tree.command(name="hello", description="Скажи здарова")
async def sayhello(interaction: discord.Interaction):
    await interaction.response.send_message("Здарова лохи")
    
@client.tree.command(name="printer", description="пишу")
async def printer(interaction: discord.Interaction, printer: str):
    await interaction.response.send_message(printer)

def ensure_json_files():
    if not os.path.exists("warns.json"):
        with open("warns.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

@client.group(name="a", invoke_without_command=True)
async def admin_group(ctx):
    embed = discord.Embed(
        title="🛡️ Панель административных команд",
        description="Используй нужную подкоманду с префиксом `!a`:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Доступные команды модерации:",
        value="`mute`, `unmute`, `ban`, `unban`, `kick`, `warn`, `unwarn`, `warn_list`",
        inline=False
    )
    await ctx.send(embed=embed)

@admin_group.command(name="mute", help="Выдать мут участнику (!a mute @user [время] [s/m/h/d] [причина])")
@commands.has_permissions(moderate_members=True)
async def admin_mute(ctx, member: discord.Member, time: int, unit: str, *, reason: str = "Без причины"):
    try:
        if ctx.author.top_role <= member.top_role and ctx.guild.owner_id != ctx.author.id:
            await ctx.send("❌ У участника роль выше или равна вашей!")
            return

        seconds = 0
        unit_text = ""
        if unit == "s":
            seconds = time
            unit_text = "сек."
        elif unit == "m":
            seconds = time * 60
            unit_text = "мин."
        elif unit == "h":
            seconds = time * 3600
            unit_text = "час."
        elif unit == "d":
            seconds = time * 86400
            unit_text = "дн."
        else:
            await ctx.send("❌ Неверный формат времени! Используйте: `s` (сек), `m` (мин), `h` (час), `d` (дн).")
            return

        duration = datetime.timedelta(seconds=seconds)
        await member.timeout(duration, reason=reason)

        emb = discord.Embed(title=f"⏳ Участнику выдан мут на {time} {unit_text}", color=discord.Color.orange())
        emb.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        emb.add_field(name="Нарушитель", value=member.mention, inline=True)
        emb.add_field(name="Причина", value=reason, inline=False)
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)
    except Exception as e:
        await ctx.send(f"❌ Ошибка при выдаче мута: {e}")
  
@admin_group.command(name="unmute", help="Снять мут с участника (!a unmute @user [причина])")
@commands.has_permissions(moderate_members=True)
async def admin_unmute(ctx, member: discord.Member, *, reason: str = "Без причины"):
    try:
        await member.timeout(None, reason=reason)
        emb = discord.Embed(title="🔊 С участника снят мут", color=discord.Color.green())
        emb.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        emb.add_field(name="Участник", value=member.mention, inline=True)
        emb.add_field(name="Причина снятия", value=reason, inline=False)
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)
    except Exception as e:
        await ctx.send(f"❌ Ошибка при размуте: {e}")
  
@admin_group.command(name="ban", help="Забанить участника навсегда или на время (!a ban @user [время] [m/h/d] [причина])")
@commands.has_permissions(ban_members=True)
async def admin_ban(ctx, member: discord.Member, time: int = None, unit: str = None, *, reason: str = "Не указана"):
    try:
        if ctx.author.top_role <= member.top_role and ctx.guild.owner_id != ctx.author.id:
            await ctx.send("❌ У игрока роль выше или равна вашей!")
            return
            
        sec, txt = 0, ""
        if time and unit:
            if unit == "m": sec, txt = time * 60, "мин."
            elif unit == "h": sec, txt = time * 3600, "час."
            elif unit == "d": sec, txt = time * 86400, "дн."
            else:
                await ctx.send("❌ Неверный формат единицы времени для бана (`m`, `h`, `d`).")
                return
            await member.ban(reason=f"Бан на {time} {txt}. Причина: {reason}")
            tit = f"⏳ Выдан временный бан на {time} {txt}"
        else:
            await member.ban(reason=f"Бан навсегда. Причина: {reason}")
            tit = "🔨 Участник забанен навсегда"
            
        emb = discord.Embed(title=tit, color=discord.Color.red())
        emb.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        emb.add_field(name="Нарушитель", value=member.mention, inline=True)
        emb.add_field(name="Причина", value=reason, inline=False)
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)
        
        if sec > 0:
            await asyncio.sleep(sec)
            try:
                await ctx.guild.unban(member, reason="Время бана истекло")
                un = discord.Embed(title="🕊️ Время бана истекло", description=f"{member.mention} был автоматически разбанен.", color=discord.Color.green())
                await ctx.send(embed=un)
            except discord.NotFound:
                pass
    except Exception as e:
        await ctx.send(f"❌ Ошибка при бане: {e}")

@admin_group.command(name="unban", help="Разбанить пользователя по ID (!a unban [ID] [причина])")
@commands.has_permissions(ban_members=True)
async def admin_unban(ctx, user_id: int, *, reason: str = "Без причины"):
    try:
        user = await client.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        emb = discord.Embed(title="🤝 Пользователь успешно разбанен", color=discord.Color.green())
        emb.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        emb.add_field(name="Пользователь", value=user.mention, inline=True)
        emb.add_field(name="Причина разбана", value=reason, inline=False)
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)
    except discord.NotFound:
        await ctx.send("❌ Этот пользователь не найден в списке банов сервера!")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при разбане: {e}")
        
@admin_group.command(name="kick", help="Кикнуть участника с сервера (!a kick @user [причина])")
@commands.has_permissions(kick_members=True)
async def admin_kick(ctx, member: discord.Member, *, reason: str = "Без причины"):
    try:
        if ctx.author.top_role <= member.top_role and ctx.guild.owner_id != ctx.author.id:
            await ctx.send("❌ Вы не можете кикнуть участника с ролью выше или равной вашей!")
            return

        await member.kick(reason=reason)
        emb = discord.Embed(title="👢 Участник кикнут с сервера", color=discord.Color.red())
        emb.add_field(name="Модератор", value=ctx.author.mention, inline=True)
        emb.add_field(name="Нарушитель", value=member.mention, inline=True)
        emb.add_field(name="Причина", value=reason, inline=False)
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)
    except Exception as e:
        await ctx.send(f"❌ Ошибка при кике: {e}")

@client.command(name="clear")
@commands.has_any_role("Персонал", "Старший персонал")
async def clear(ctx, amount: int):
    if amount < 1:
        await ctx.send("Укажите число больше 0")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"Успешно удалено {len(deleted) - 1} сообщений", delete_after=5)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("У вас нет прав для использования этой команды")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("У меня нет прав на управление сообщениями. Проверьте настройки канала/бота")

@admin_group.command(name="warn", help="Выдать варн участнику (!a warn @user [причина])")
@commands.has_any_role("Scarletᵒʷⁿᵉʳ", "Co-Owner", "Curator", "Staff Manager")
async def admin_warn(ctx, member: discord.Member, *, reason: str = "Без причины"):
    ensure_json_files()
    
    with open("warns.json", "r", encoding="utf-8") as f:
        warns_data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id not in warns_data:
        warns_data[guild_id] = {}

    if user_id not in warns_data[guild_id]:
        warns_data[guild_id][user_id] = {"count": 0, "reasons": []}

    warns_data[guild_id][user_id]["count"] += 1
    warns_data[guild_id][user_id]["reasons"].append(reason)
    
    current_warns = warns_data[guild_id][user_id]["count"]

    with open("warns.json", "w", encoding="utf-8") as f:
        json.dump(warns_data, f, indent=4, ensure_ascii=False)

    if current_warns >= 3:
        warns_data[guild_id][user_id] = {"count": 0, "reasons": []}
        with open("warns.json", "w", encoding="utf-8") as f:
            json.dump(warns_data, f, indent=4, ensure_ascii=False)
            
        try:
            ban_duration_seconds = 5 * 86400
            await member.ban(reason=f"Автоматический бан за 3/3 предупреждений. Последняя причина: {reason}")

            emb = discord.Embed(title="🔨 Автоматический временный бан", color=discord.Color.red())
            emb.add_field(name="Администратор", value=ctx.author.mention, inline=True)
            emb.add_field(name="Нарушитель", value=member.mention, inline=True)
            emb.add_field(name="Срок бана", value="`5 дней` (3/3 варнов)", inline=False)
            emb.add_field(name="Последняя причина", value=reason, inline=False)
            emb.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=emb)

            await asyncio.sleep(ban_duration_seconds)
            try:
                await ctx.guild.unban(member, reason="Истек срок автоматического бана за 3/3 варнов")
                un = discord.Embed(
                    title="🕊️ Срок бана истек", 
                    description=f"Пользователь {member.mention} был автоматически разбанен после 5 дней бана.", 
                    color=discord.Color.green()
                )
                await ctx.send(embed=un)
            except discord.NotFound:
                pass

        except Exception as e:
            await ctx.send(f"❌ Не удалось забанить пользователя: {e}")
    else:
        emb = discord.Embed(title="⚠️ Выдано предупреждение", color=discord.Color.yellow())
        emb.add_field(name="Администратор", value=ctx.author.mention, inline=True)
        emb.add_field(name="Нарушитель", value=member.mention, inline=True)
        emb.add_field(name="Причина", value=reason, inline=False)
        emb.add_field(name="Предупреждения", value=f"`{current_warns}/3`", inline=False)
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)

@admin_group.command(name="unwarn", help="Снять варн с участника (!a unwarn @user [причина снятия])")
@commands.has_any_role("Scarletᵒʷⁿᵉʳ", "Co-Owner", "Curator", "Staff Manager")
async def admin_unwarn(ctx, member: discord.Member, *, reason: str = "Без причины"):
    ensure_json_files()
    
    with open("warns.json", "r", encoding="utf-8") as f:
        warns_data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id not in warns_data or user_id not in warns_data[guild_id]:
        await ctx.send(f"❌ У пользователя {member.mention} нет активных предупреждений!")
        return

    user_data = warns_data[guild_id][user_id]

    if isinstance(user_data, int):
        count = user_data
        reasons = []
    else:
        count = user_data.get("count", 0)
        reasons = user_data.get("reasons", [])

    if count <= 0:
        await ctx.send(f"❌ У пользователя {member.mention} нет активных предупреждений!")
        return

    count -= 1
    if reasons:
        reasons.pop()

    warns_data[guild_id][user_id] = {
        "count": count,
        "reasons": reasons
    }

    with open("warns.json", "w", encoding="utf-8") as f:
        json.dump(warns_data, f, indent=4, ensure_ascii=False)

    emb = discord.Embed(title="✅ Снято предупреждение", color=discord.Color.green())
    emb.add_field(name="Администратор", value=ctx.author.mention, inline=True)
    emb.add_field(name="Нарушитель", value=member.mention, inline=True)
    emb.add_field(name="Причина снятия", value=reason, inline=False)
    emb.add_field(name="Осталось предупреждений", value=f"`{count}/3`", inline=False)
    emb.timestamp = datetime.datetime.utcnow()
    await ctx.send(embed=emb)
    
@admin_group.command(name="warn_list", aliases=["warn list"], help="Посмотреть список всех варнов на сервере (!a warn list)")
@commands.has_any_role("Scarletᵒʷⁿᵉʳ", "Co-Owner", "Curator", "Staff Manager")
async def admin_warn_list(ctx):
    ensure_json_files()
    gid = str(ctx.guild.id)
    
    with open("warns.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if gid not in data or not data[gid]:
        await ctx.send("❌ На сервере пока нет активных варнов.")
        return

    embed = discord.Embed(title="📋 Список активных предупреждений", color=discord.Color.red())
    
    found = False
    for uid, info in data[gid].items():
        if isinstance(info, int):
            count = info
            reasons = ["Причина не указана"] * count
        else:
            count = info.get("count", 0)
            reasons = info.get("reasons", [])

        if count > 0:
            member = ctx.guild.get_member(int(uid))
            mention = member.mention if member else f"Пользователь ID: {uid}"
            
            reasons_text = "\n".join([f"{i+1} варн за {rs}" for i, rs in enumerate(reasons)])
            
            embed.add_field(
                name=f"{member.display_name if member else uid} ({count}/3)",
                value=f"{mention}\n{reasons_text}",
                inline=False
            )
            found = True
    
    if not found:
        await ctx.send("❌ На сервере пока нет активных варнов.")
    else:
        await ctx.send(embed=embed)

@admin_warn_list.error
async def warn_list_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("У вас нет прав для использования этой команды!")

@client.command(name="balance")
async def balance(ctx):
    file_path = "economy.json"
    
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
            with open(file_path, "w", encoding="utf-8") as fw:
                json.dump(data, fw)

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    user_data = data.get(guild_id, {}).get(user_id, {})
    
    cash = user_data.get("balance", 0)
    bank = user_data.get("bank", 0)
    total = cash + bank

    embed = discord.Embed(
        title=f"Баланс {ctx.author.display_name}", 
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    
    embed.add_field(name="Кошелек", value=f"{cash:,}$", inline=False)
    embed.add_field(name="Банковский счет", value=f"{bank:,}$", inline=False)
    embed.add_field(name="Итого", value=f"{total:,}$", inline=False)

    await ctx.send(embed=embed)
    
@client.tree.command(name="deposit", description="Положить деньги в банк")
async def deposit(interaction: discord.Interaction, amount: str):
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    with open("economy.json", "r") as f:
        data = json.load(f)
    if guild_id not in data or user_id not in data[guild_id]:
        await interaction.response.send_message("У вас нет аккаунта")
        return
    cash = data[guild_id][user_id].get("balance", 0)
    bank = data[guild_id][user_id].get("bank", 0)
    if amount.lower() == "all":
        to_deposit = cash
    else:
        try:
            to_deposit = int(amount)
        except:
            await interaction.response.send_message("Введите число или all")
            return
    if to_deposit > cash:
        await interaction.response.send_message("Недостаточно денег")
        return
    if to_deposit <= 0:
        await interaction.response.send_message("Сумма должна быть больше 0")
        return
    data[guild_id][user_id]["balance"] = cash - to_deposit
    data[guild_id][user_id]["bank"] = bank + to_deposit
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)
    cash = data[guild_id][user_id]["balance"]
    bank = data[guild_id][user_id]["bank"]
    total = cash + bank
    embed = discord.Embed(title=f"Баланс {interaction.user.display_name}", color=discord.Color.green())
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="Кошелек", value=f"{cash:,}$", inline=False)
    embed.add_field(name="Банковский счет", value=f"{bank:,}$", inline=False)
    embed.add_field(name="Итого", value=f"{total:,}$", inline=False)
    await interaction.response.send_message(content=f"Вы внесли {to_deposit:,}$", embed=embed)

@client.tree.command(name="withdraw", description="Снять деньги с банка (Сумма или all)")
async def withdraw(interaction: discord.Interaction, amount: str):
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    with open("economy.json", "r") as f:
        data = json.load(f)
    if guild_id not in data or user_id not in data[guild_id]:
        await interaction.response.send_message("У вас нет аккаунта")
        return
    cash = data[guild_id][user_id].get("balance", 0)
    bank = data[guild_id][user_id].get("bank", 0)
    if amount.lower() == "all":
        to_withdraw = bank
    else:
        try:
            to_withdraw = int(amount)
        except:
            await interaction.response.send_message("Введите число или all")
            return
    if to_withdraw > bank:
        await interaction.response.send_message("Недостаточно денег в банке")
        return
    if to_withdraw <= 0:
        await interaction.response.send_message("Сумма должна быть больше 0")
        return
    data[guild_id][user_id]["bank"] = bank - to_withdraw
    data[guild_id][user_id]["balance"] = cash + to_withdraw
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)
    cash = data[guild_id][user_id]["balance"]
    bank = data[guild_id][user_id]["bank"]
    total = cash + bank
    embed = discord.Embed(title=f"Баланс {interaction.user.display_name}", color=discord.Color.green())
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="Кошелек", value=f"{cash:,}$", inline=False)
    embed.add_field(name="Банковский счет", value=f"{bank:,}$", inline=False)
    embed.add_field(name="Итого", value=f"{total:,}$", inline=False)
    await interaction.response.send_message(content=f"Вы сняли {to_withdraw:,}$", embed=embed)

import math

class LeaderboardView(discord.ui.View):
    def __init__(self, data, page=0):
        super().__init__(timeout=60)
        self.data = data
        self.page = page
        self.items_per_page = 10
        self.max_pages = math.ceil(len(data) / self.items_per_page)

    def get_embed(self):
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        page_data = self.data[start:end]

        emb = discord.Embed(title=f"🧳 Лидеры: Общий Капитал | Страница {self.page + 1}", color=discord.Color.blue())
        
        desc = ""
        for index, (user_id, data) in enumerate(page_data, start=start + 1):
            bal = data.get("balance", 0)
            desc += f"🏅 **{index}.** <@{user_id}>\n💵 **{bal:,} :red_crystal:**\n\n"
        
        emb.description = desc if desc else "Пусто"
        return emb

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_pages - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

@client.command(name="leaderboard")
async def leaderboard(ctx):
    file_path = "economy.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    server_data = data.get(str(ctx.guild.id), {})
    
    sorted_users = sorted(
        [(uid, udata) for uid, udata in server_data.items() if udata.get("balance", 0) >= 1],
        key=lambda item: item[1].get("balance", 0), 
        reverse=True
    )

    if not sorted_users:
        return await ctx.send("❌ Таблица лидеров пуста!")

    view = LeaderboardView(sorted_users)
    await ctx.send(embed=view.get_embed(), view=view)

@client.tree.command(name="weekly", description="Получить еженедельную награду")
async def weekly(interaction: discord.Interaction):
    economy_data = {}
    if os.path.exists("economy.json"):
        with open("economy.json", "r") as f:
            economy_data = json.load(f)

    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    if guild_id not in economy_data:
        economy_data[guild_id] = {}
    if user_id not in economy_data[guild_id]:
        economy_data[guild_id][user_id] = {"balance": 0, "last_daily": 0, "last_weekly": 0, "last_work": 0, "last_training": 0, "streak": 0}

    user_data = economy_data[guild_id][user_id]
    current_time = int(time.time())
    cooldown = 604800

    if current_time - user_data.get("last_weekly", 0) < cooldown:
        remains = cooldown - (current_time - user_data.get("last_weekly", 0))
        days = remains // 86400
        hours = (remains % 86400) // 3600
        await interaction.response.send_message(f"❌ Награда будет доступна через `{days}д {hours}ч`", ephemeral=True)
        return

    user_data["balance"] += 25000
    user_data["last_weekly"] = current_time

    with open("economy.json", "w") as f:
        json.dump(economy_data, f, indent=4)

    emb = discord.Embed(
        title="🎁 Еженедельный бонус",
        description=(
            f"Поздравляем! **{interaction.user.display_name}** получил(а) бонус в размере **25,000**!\n\n"
            f"**Следующий еженедельный бонус будет доступен:**\n`через неделю`"
        ),
        color=discord.Color.blue(),
        timestamp=interaction.created_at
    )
    
    if interaction.user.avatar:
        emb.set_thumbnail(url=interaction.user.avatar.url)
        
    guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
    emb.set_footer(text=interaction.guild.name, icon_url=guild_icon)

    await interaction.response.send_message(embed=emb)

@client.tree.command(name="daily", description="Получить ежедневную награду")
async def daily(interaction: discord.Interaction):
    economy_data = {}
    if os.path.exists("economy.json"):
        with open("economy.json", "r") as f:
            economy_data = json.load(f)

    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    if guild_id not in economy_data:
        economy_data[guild_id] = {}
    if user_id not in economy_data[guild_id]:
        economy_data[guild_id][user_id] = {"balance": 0, "last_daily": 0, "last_weekly": 0, "last_work": 0, "last_training": 0, "streak": 0}

    user_data = economy_data[guild_id][user_id]
    current_time = int(time.time())
    cooldown = 86400
    last_daily = user_data.get("last_daily", 0)

    if current_time - last_daily < cooldown:
        remains = cooldown - (current_time - last_daily)
        hours = remains // 3600
        minutes = (remains % 3600) // 60
        await interaction.response.send_message(f"❌ Награда будет доступна через `{hours}ч {minutes}м`", ephemeral=True)
        return

    streak = user_data.get("streak", 0)
    if current_time - last_daily < 172800:
        streak += 1
    else:
        streak = 1

    user_data["balance"] += 5000
    user_data["last_daily"] = current_time
    user_data["streak"] = streak

    with open("economy.json", "w") as f:
        json.dump(economy_data, f, indent=4)

    emb = discord.Embed(
        title="🎁 Ежедневный бонус",
        description=(
            f"Поздравляем! **{interaction.user.display_name}** получил(а) бонус в размере **5,000**!\n\n"
            f"**Текущий стрик: {streak} 🔥**\n\n"
            f"**Следующий ежедневный бонус будет доступен:**\n`через день`"
        ),
        color=discord.Color.green(),
        timestamp=interaction.created_at
    )
    
    if interaction.user.avatar:
        emb.set_thumbnail(url=interaction.user.avatar.url)
    guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
    emb.set_footer(text=interaction.guild.name, icon_url=guild_icon)

    await interaction.response.send_message(embed=emb)

@client.tree.command(name="work", description="Устроиться на подработку")
async def work(interaction: discord.Interaction):
    economy_data = {}
    if os.path.exists("economy.json"):
        with open("economy.json", "r") as f:
            economy_data = json.load(f)

    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    if guild_id not in economy_data:
        economy_data[guild_id] = {}
    if user_id not in economy_data[guild_id]:
        economy_data[guild_id][user_id] = {"balance": 0, "last_daily": 0, "last_weekly": 0, "last_work": 0, "last_training": 0}

    user_data = economy_data[guild_id][user_id]
    current_time = int(time.time())
    cooldown = 1800

    if current_time - user_data.get("last_work", 0) < cooldown:
        remains = cooldown - (current_time - user_data.get("last_work", 0))
        minutes = remains // 60
        seconds = remains % 60
        await interaction.response.send_message(f"❌ Вы устали! Отдохните ещё `{minutes}м {seconds}с`", ephemeral=True)
        return

    earned = random.randint(50, 100)
    user_data["balance"] += earned
    user_data["last_work"] = current_time

    with open("economy.json", "w") as f:
        json.dump(economy_data, f, indent=4)

    emb = discord.Embed(title="💼 Работа", description=f"Вы успешно поработали и получили `{earned}` 💎 кристаликсов!", color=discord.Color.blue())
    await interaction.response.send_message(embed=emb)

@client.tree.command(name="pay", description="Перевести кристаликсы другому пользователю")
async def pay(interaction: discord.Interaction, member: discord.Member, amount: int):
    if member == interaction.user:
        await interaction.response.send_message("❌ Нельзя перевести кристаликсы самому себе!", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("❌ Сумма должна быть больше 0!", ephemeral=True)
        return

    if amount > 1000000000:
        await interaction.response.send_message("❌ Максимальная сумма перевода — 1,000,000,000 кристаликсов!", ephemeral=True)
        return

    economy_data = {}
    if os.path.exists("economy.json"):
        with open("economy.json", "r") as f:
            economy_data = json.load(f)

    guild_id = str(interaction.guild.id)
    sender_id = str(interaction.user.id)
    receiver_id = str(member.id)

    if guild_id not in economy_data:
        economy_data[guild_id] = {}
    
    if sender_id not in economy_data[guild_id]:
        economy_data[guild_id][sender_id] = {"balance": 0, "last_daily": 0, "last_weekly": 0, "last_work": 0, "last_training": 0, "streak": 0}
    
    if receiver_id not in economy_data[guild_id]:
        economy_data[guild_id][receiver_id] = {"balance": 0, "last_daily": 0, "last_weekly": 0, "last_work": 0, "last_training": 0, "streak": 0}

    if economy_data[guild_id][sender_id]["balance"] < amount:
        await interaction.response.send_message("❌ У вас недостаточно кристаликсов для этого перевода!", ephemeral=True)
        return

    economy_data[guild_id][sender_id]["balance"] -= amount
    economy_data[guild_id][receiver_id]["balance"] += amount

    with open("economy.json", "w") as f:
        json.dump(economy_data, f, indent=4)
    
    emb = discord.Embed(
        title="💸 Перевод средств",
        description=f"**{interaction.user.mention}** перевел(а) **{amount:,} :red_crystal:** пользователю **{member.mention}**!",
        color=discord.Color.green()
    )
    
    await interaction.response.send_message(embed=emb)
    


multipliers = {
    "🍒": 2,
    "🍋": 3,
    "🍊": 4,
    "🍇": 5,
    "🔔": 10
}

@client.command(name="slots")
async def slots(ctx, bet: int):
    await ctx.send(f"{ctx.author.mention} поставил {bet}")

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if bet < 1000 or bet > 1000000000:
        await ctx.send("Ставка от 1000 до 1 000 000 000")
        return

    with open("economy.json", "r") as f:
        data = json.load(f)

    if guild_id not in data:
        data[guild_id] = {}
    if user_id not in data[guild_id]:
        data[guild_id][user_id] = {"balance": 0}

    cash = data[guild_id][user_id].get("balance", 0)

    if bet > cash:
        await ctx.send("Недостаточно средств")
        return

    outcome = random.choices(["lose", "partial", "jackpot"], weights=[56, 35, 9], k=1)[0]
    items = ["🍒", "🍋", "🍊", "🍇", "🔔"]
    multipliers = {"🍒": 2, "🍋": 3, "🍊": 4, "🍇": 5, "🔔": 10}
    
    if outcome == "lose":
        result = random.sample(items, 3)
        while result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            result = random.sample(items, 3)
        win_delta = -bet
        msg = f"Проигрыш. Вы потеряли {bet:,}$"
    elif outcome == "partial":
        pair = random.choice(items)
        result = [pair, pair, random.choice([x for x in items if x != pair])]
        random.shuffle(result)
        win_delta = int(bet * 0.5)
        msg = f"Хорошо! Два совпадения, вы выиграли {int(bet * 1.5):,}$"
    else:
        sym = random.choice(items)
        result = [sym, sym, sym]
        mult = multipliers[sym]
        win_delta = bet * (mult - 1)
        msg = f"Джекпот! Вы выиграли {bet * mult:,}$ (x{mult})"
        
        role = discord.utils.get(ctx.guild.roles, name="Азартный Мастер")
        if role and role not in ctx.author.roles:
            if random.random() < random.uniform(0.005, 0.01):
                await ctx.author.add_roles(role)
                try:
                    await ctx.author.send(f"🎉 Поздравляю! Ты получил роль **Азартный Мастер** на сервере {ctx.guild.name}!")
                    msg += "\n🎲 Ты получил секретную роль Азартный Мастер! (проверь ЛС)"
                except:
                    msg += "\n🎲 Ты получил секретную роль Азартный Мастер!"

    data[guild_id][user_id]["balance"] = cash + win_delta

    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)

    embed = discord.Embed(title="Казино Слоты", color=discord.Color.gold())
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.add_field(name="Результат", value=f"{result[0]} {result[1]} {result[2]}", inline=False)
    embed.add_field(name="Итог", value=msg, inline=False)
    embed.add_field(name="Ваш баланс", value=f"{data[guild_id][user_id]['balance']:,}$", inline=False)

    await ctx.send(embed=embed)

def get_cards_str(hand):
    suits = ["♠", "♥", "♦", "♣"]
    cards = []
    for val in hand:
        suit = random.choice(suits)
        name = str(val)
        if val == 11: name = "J"
        if val == 12: name = "Q"
        if val == 13: name = "K"
        if val == 14: name = "A"
        cards.append(f"{name}{suit}")
    return " ".join(cards)

def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        if card > 10: val = 10
        elif card == 14: val = 11
        else: val = card
        score += val
        if card == 14: aces += 1
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

class BlackjackView(discord.ui.View):
    def __init__(self, user, bet, gid, uid, data):
        super().__init__(timeout=60)
        self.user = user
        self.bet = bet
        self.gid = gid
        self.uid = uid
        self.data = data
        self.player_hand = [random.randint(2, 14), random.randint(2, 14)]
        self.dealer_hand = [random.randint(2, 14), random.randint(2, 14)]

async def end_game(self, interaction, result_text, win_status="loss"):
    p_score = calculate_score(self.player_hand)
    d_score = calculate_score(self.dealer_hand)
        
    embed = discord.Embed(title="БлекДжек", color=0x2f3136)
    embed.add_field(name="Ваши карты:", value=f"{get_cards_str(self.player_hand)} ({p_score})", inline=False)
    embed.add_field(name="Карты дилера:", value=f"{get_cards_str(self.dealer_hand)} ({d_score})", inline=False)
    embed.add_field(name="Итог", value=result_text, inline=False)
        
    if win_status == "win":
        self.data[self.gid][self.uid]["balance"] += self.bet * 2
    elif win_status == "draw":
        self.data[self.gid][self.uid]["balance"] += self.bet
        
    save_data(self.data)
    await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Взять", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_hand.append(random.randint(2, 14))
        if calculate_score(self.player_hand) > 21:
            await self.end_game(interaction, f"Перебор! Вы потеряли {self.bet:,}$", win=False)
        else:
            p_score = calculate_score(self.player_hand)
            embed = discord.Embed(title="БлекДжек", color=0x2f3136)
            embed.add_field(name="Ваши карты:", value=f"{get_cards_str(self.player_hand)} ({p_score})", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Хватит", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        while calculate_score(self.dealer_hand) < 17:
            self.dealer_hand.append(random.randint(2, 14))
        
        p_score = calculate_score(self.player_hand)
        d_score = calculate_score(self.dealer_hand)
        
        if d_score > 21 or p_score > d_score:
            await self.end_game(interaction, f"Вы выиграли {self.bet:,}$!", win=True)
        elif p_score < d_score:
            await self.end_game(interaction, f"Вы проиграли {self.bet:,}$", win=False)
        else:
            await self.end_game(interaction, "Ничья! Деньги возвращены.", win=None)

@client.tree.command(name="blackjack", description="Сыграть в БлэкДжек")
async def blackjack(interaction: discord.Interaction, bet: int):
    gid, uid = str(interaction.guild_id), str(interaction.user.id)
    
    with open("economy.json", "r") as f:
        data = json.load(f)
    
    if gid not in data: data[gid] = {}
    if uid not in data[gid]: data[gid][uid] = {"balance": 0}
    
    balance = data[gid][uid].get("balance", 0)

    if bet < 1000 or bet > 1000000000:
        await interaction.response.send_message("Ставка от 1000 до 1 000 000 000", ephemeral=True)
        return

    if bet > balance:
        await interaction.response.send_message("Недостаточно средств", ephemeral=True)
        return
    
    data[gid][uid]["balance"] -= bet
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)
    
    view = BlackjackView(interaction.user, bet, gid, uid)
    await interaction.response.send_message("Игра началась!", view=view)

crime_cooldowns = {}

@client.tree.command(name="crime", description="Ограбить пользователя")
async def crime(interaction: discord.Interaction, member: discord.Member):
    uid = str(interaction.user.id)
    gid = str(interaction.guild_id)
    current_time = time.time()

    if member == interaction.user:
        await interaction.response.send_message("Нельзя грабить самого себя", ephemeral=True)
        return

    if member.bot:
        await interaction.response.send_message("Нельзя грабить бота", ephemeral=True)
        return

    if uid in crime_cooldowns and current_time - crime_cooldowns[uid] < 3600:
        wait_time = int(3600 - (current_time - crime_cooldowns[uid]))
        minutes = wait_time // 60
        seconds = wait_time % 60
        await interaction.response.send_message(f"Кулдаун! Попробуйте через {minutes} мин. {seconds} сек.", ephemeral=True)
        return

    data = load_data()
    if gid not in data: data[gid] = {}
    if uid not in data[gid]: data[gid][uid] = {"balance": 0, "businesses": []}
    
    crime_cooldowns[uid] = current_time
    success = random.random() < 0.40
    amount = random.randint(1000, 2000)

    if success:
        data[gid][uid]["balance"] += amount
        message = f"Успешное ограбление! Вы украли {amount}$ у {member.mention}"
    else:
        data[gid][uid]["balance"] -= amount
        message = f"Вас поймали! Вы потеряли {amount}$"

    save_data(data)
    await interaction.response.send_message(message)

def decl(number, forms):
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        return forms[2]
    return forms[cases[min(number % 10, 5)]]

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()

    @discord.ui.button(label="Принять участие", style=discord.ButtonStyle.green, custom_id="join_giveaway")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("Вы уже участвуете!", ephemeral=True)
            return
        self.participants.add(interaction.user.id)
        await interaction.response.send_message("Вы успешно записались на розыгрыш!", ephemeral=True)

@client.tree.command(name="gstart", description="Создать розыгрыш")
@app_commands.checks.has_any_role("Project Leaders", "Main Administrator", "Administrator", "Master Eventer", "Eventer")
async def gstart(interaction: discord.Interaction, duration: str, winners: int, prize: str):
    total_seconds = 0
    if "d" in duration: total_seconds = int(duration.replace("d", "")) * 86400
    elif "h" in duration: total_seconds = int(duration.replace("h", "")) * 3600
    elif "m" in duration: total_seconds = int(duration.replace("m", "")) * 60
    elif "s" in duration: total_seconds = int(duration.replace("s", ""))
    else: total_seconds = int(duration) * 60

    if total_seconds > 31 * 86400:
        await interaction.response.send_message("Максимальная длительность — 31 день!", ephemeral=True)
        return
    
    view = GiveawayView()
    embed = discord.Embed(title=f"🎉 {prize}", color=discord.Color.blue())
    embed.add_field(name="Участников", value="0", inline=True)
    embed.add_field(name="Осталось", value="...", inline=True)
    
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()

    end_time = discord.utils.utcnow() + datetime.timedelta(seconds=total_seconds)

    while discord.utils.utcnow() < end_time:
        remaining = end_time - discord.utils.utcnow()
        total_rem = int(remaining.total_seconds())
        d, rem = divmod(total_rem, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        time_text = f"{d}d {h}h {m}m {s}s"
        
        embed.set_field_at(0, name="Участников", value=str(len(view.participants)), inline=True)
        embed.set_field_at(1, name="Осталось", value=time_text, inline=True)
        await msg.edit(embed=embed)
        await asyncio.sleep(1)

    participants = list(view.participants)
    if len(participants) < winners:
        await msg.reply("Недостаточно участников!")
        return

    winners_list = []
    temp_participants = participants[:]
    
    for _ in range(winners):
        if not temp_participants: break
        found_winner = None
        for uid in temp_participants:
            member = interaction.guild.get_member(uid)
            if member and any(r.id == ROLE_LOOT_STASH_LIMIT_ID for r in member.roles):
                if random.random() <= 0.25:
                    found_winner = uid
                    break
        
        if not found_winner:
            found_winner = random.choice(temp_participants)
            
        winners_list.append(found_winner)
        temp_participants.remove(found_winner)
    
    mentions = ", ".join([f"<@{w_id}>" for w_id in winners_list])
    embed.title = f"Розыгрыш завершен: {prize}"
    embed.description = f"Победители: {mentions}"
    embed.color = discord.Color.gold()
    await msg.edit(embed=embed, view=None)
    await msg.reply(f"Поздравляем: {mentions}!")

user_data = {}
voice_timers = {}

DATA_FILE = "death_note_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "cooldowns": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

storage = load_data()
user_data = storage["users"]
cooldowns = storage["cooldowns"]

class FactionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Кира", style=discord.ButtonStyle.danger, emoji="🍎", custom_id="faction_kira_button")
    async def kira(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data[str(interaction.user.id)] = {"side": "kira", "messages": 0, "commands": 0, "voice": 0}
        await interaction.response.send_message("Ты примкнул к Кире!", ephemeral=True)

    @discord.ui.button(label="Детектив", style=discord.ButtonStyle.primary, emoji="🕵️", custom_id="faction_detective_button")
    async def detective(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data[str(interaction.user.id)] = {"side": "detective", "messages": 0, "commands": 0, "voice": 0}
        await interaction.response.send_message("Ты стал на сторону Детективов!", ephemeral=True)

@client.event
async def on_message(message):
    if message.author.bot: return
    uid = str(message.author.id)
    if uid in user_data and message.channel.name == "общее":
        user_data[uid]['messages'] = min(user_data[uid].get('messages', 0) + 1, 150)
        save_data({"users": user_data, "cooldowns": cooldowns})
    await client.process_commands(message)

@client.event
async def on_command_completion(ctx):
    uid = str(ctx.author.id)
    if uid in user_data:
        user_data[uid]['commands'] = min(user_data[uid].get('commands', 0) + 1, 50)

@client.event
async def on_voice_state_update(member, before, after):
    uid = str(member.id)
    if uid not in user_data: return
    if before.channel is None and after.channel is not None:
        voice_timers[uid] = time.time()
    elif before.channel is not None and after.channel is None:
        if uid in voice_timers:
            duration = (time.time() - voice_timers[uid]) / 60
            user_data[uid]['voice'] = min(user_data[uid].get('voice', 0) + int(duration), 20)
            del voice_timers[uid]

cooldowns = {}

@client.group(invoke_without_command=True)
async def event(ctx):
    uid = str(ctx.author.id)
    if uid in user_data:
        data = user_data[uid]
        now = time.time()
        
        if uid in cooldowns and now - cooldowns[uid] < 1800:
            wait_time = int((1800 - (now - cooldowns[uid])) / 60)
            await ctx.send(f"⚠️ Задания на перезарядке. Подожди еще {wait_time} мин.")
            return

        if data['messages'] >= 150 and data['commands'] >= 50 and data['voice'] >= 20:
            data['messages'] = 0
            data['commands'] = 0
            data['voice'] = 0
            cooldowns[uid] = now
            await ctx.send("✅ Задания выполнены! Таймер перезарядки (30 мин) запущен.")
            return

        m, c, v = data.get('messages', 0), data.get('commands', 0), data.get('voice', 0)
        bar_v = f"[{'▬' * (v // 4)}{'—' * (5 - (v // 4))}]"
        bar_c = f"[{'▬' * (c // 10)}{'—' * (5 - (c // 10))}]"
        bar_m = f"[{'▬' * (m // 30)}{'—' * (5 - (m // 30))}]"

        tasks = ("Охота", "Тетрадь", "Слухи") if data['side'] == 'kira' else ("Допросы", "Улики", "Поиск")

        embed = discord.Embed(title=f"🍎 Фракция: {data['side'].upper()}", color=0xff0000 if data['side'] == 'kira' else 0x0000ff)
        embed.description = f"🎙️ {tasks[0]}: {bar_v} {v}/20\n🔮 {tasks[1]}: {bar_c} {c}/50\n🩸 {tasks[2]}: {bar_m} {m}/150"
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="📓 DEATH NOTE: ВОЙНА ФРАКЦИЙ", color=0xffff00)
        embed.description = "ВЫБЕРИ СВОЮ СТОРОНУ. ПУТИ НАЗАД НЕ БУДЕТ."
        await ctx.send(embed=embed, view=FactionView())

@event.command(name="leaderboard")
async def event_leaderboard(ctx):
    await ctx.guild.chunk()
    kira_list = []
    det_list = []
    for uid, data in user_data.items():
        score = data.get('messages', 0) + data.get('commands', 0) + data.get('voice', 0)
        member = ctx.guild.get_member(int(uid))
        name = member.display_name if member else f"ID {uid}"
        if data.get('side') == 'kira':
            kira_list.append((name, score))
        else:
            det_list.append((name, score))
    kira_list.sort(key=lambda x: x[1], reverse=True)
    det_list.sort(key=lambda x: x[1], reverse=True)
    k_text = "\n".join([f"{i+1}. {n} — {s}" for i, (n, s) in enumerate(kira_list[:5])]) or "Пусто."
    d_text = "\n".join([f"{i+1}. {n} — {s}" for i, (n, s) in enumerate(det_list[:5])]) or "Пусто."
    embed = discord.Embed(title="🏆 ТАБЛИЦА ЛИДЕРОВ", color=0xffff00)
    embed.add_field(name="🍎 Кира", value=k_text, inline=True)
    embed.add_field(name="🕵️ Детективы", value=d_text, inline=True)
    await ctx.send(embed=embed)

@client.event
async def on_ready():
    client.add_view(FactionView())

business = app_commands.Group(name="business", description="Управление бизнесом")

client.tree.add_command(business)

def load_data():
    if not os.path.exists("economy.json"): return {}
    with open("economy.json", "r") as f: return json.load(f)

def save_data(data):
    with open("economy.json", "w") as f: json.dump(data, f, indent=4)

BUSINESS_PRICES = {
    1: 100000,
    2: 250000,
    3: 750000
}

def check_user(data, gid, uid):
    if gid not in data:
        data[gid] = {}
    if uid not in data[gid]:
        data[gid][uid] = {"balance": 0, "businesses": []}
    if "businesses" not in data[gid][uid]:
        data[gid][uid]["businesses"] = []
    if "balance" not in data[gid][uid]:
        data[gid][uid]["balance"] = 0

@business.command(name="create", description="Создать свой бизнес")
@app_commands.choices(level=[
    app_commands.Choice(name="Уровень 1 (100к)", value=1),
    app_commands.Choice(name="Уровень 2 (250к)", value=2),
    app_commands.Choice(name="Уровень 3 (750к)", value=3),
])
async def create(interaction: discord.Interaction, name: str, level: int):
    cost = BUSINESS_PRICES.get(level)
    gid, uid = str(interaction.guild_id), str(interaction.user.id)
    data = load_data()
    
    check_user(data, gid, uid)
    
    if len(data[gid][uid]["businesses"]) >= 3:
        await interaction.response.send_message("У вас уже максимум (3) бизнесов!", ephemeral=True)
        return

    balance = data[gid][uid].get("balance", 0)
    
    if balance < cost:
        await interaction.response.send_message("Недостаточно средств!", ephemeral=True)
        return

    data[gid][uid]["balance"] -= cost
    data[gid][uid]["businesses"].append({
        "name": name, 
        "level": level, 
        "last_collect": time.time()
    })
    
    save_data(data)
    await interaction.response.send_message(f"Бизнес '{name}' создан!")

@business.command(name="delete_player", description="Удалить бизнес игрока")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.choices(choice=[
    app_commands.Choice(name="1", value="1"),
    app_commands.Choice(name="2", value="2"),
    app_commands.Choice(name="3", value="3"),
    app_commands.Choice(name="All", value="all"),
])
async def delete_player(interaction: discord.Interaction, user: discord.Member, choice: str):
    data = load_data()
    gid, uid = str(interaction.guild_id), str(user.id)
    if gid not in data or uid not in data[gid] or not data[gid][uid].get("businesses"):
        await interaction.response.send_message("У игрока нет бизнесов.", ephemeral=True)
        return
    businesses = data[gid][uid]["businesses"]
    if choice == "all":
        data[gid][uid]["businesses"] = []
        msg = f"Все бизнесы игрока {user.name} удалены."
    else:
        index = int(choice) - 1
        if 0 <= index < len(businesses):
            removed_biz = businesses.pop(index)
            msg = f"Бизнес '{removed_biz['name']}' игрока {user.name} удален."
        else:
            await interaction.response.send_message(f"У игрока нет бизнеса №{choice}.", ephemeral=True)
            return
    save_data(data)
    await interaction.response.send_message(msg)

@delete_player.error
async def delete_player_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("У вас нет прав администратора!", ephemeral=True)

@business.command(name="collect", description="Собрать прибыль")
async def collect_biz(interaction: discord.Interaction):
    await interaction.response.defer()
    
    guild_id, user_id = str(interaction.guild_id), str(interaction.user.id)
    
    if not os.path.exists("economy.json"):
        await interaction.followup.send("Файл экономики не найден.", ephemeral=True)
        return

    with open("economy.json", "r") as f:
        data = json.load(f)
    
    user_data = data.get(guild_id, {}).get(user_id)
    if not user_data or not user_data.get("businesses"):
        await interaction.followup.send("У вас нет бизнесов для сбора прибыли.", ephemeral=True)
        return

    now = datetime.datetime.now()
    total_profit = 0
    updated = False
    
    for biz in user_data["businesses"]:
        profit = BUSINESS_LEVELS[biz.get("level", 1)]["profit"]
        raw_last_collect = biz.get("last_collect") or biz.get("created_at")
        
        if isinstance(raw_last_collect, str):
            try:
                last_collect = datetime.datetime.fromisoformat(raw_last_collect)
            except ValueError:
                last_collect = now
                biz["last_collect"] = now.isoformat()
                updated = True
        else:
            last_collect = now
            biz["last_collect"] = now.isoformat()
            updated = True
        
        minutes_passed = (now - last_collect).total_seconds() / 60
        intervals = int(minutes_passed // 5)
        
        if intervals > 0:
            total_profit += intervals * profit
            biz["last_collect"] = (last_collect + datetime.timedelta(minutes=intervals * 5)).isoformat()
            updated = True
    
    if total_profit <= 0:
        await interaction.followup.send("Прибыль еще не накопилась!", ephemeral=True)
        return
        
    user_data["balance"] = user_data.get("balance", 0) + total_profit
    
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await interaction.followup.send(f"Вы успешно собрали {total_profit:,}$!")

@business.command(name="list", description="Список ваших бизнесов")
async def list_biz(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    
    if not os.path.exists("economy.json"):
        await interaction.response.send_message("База данных экономики пуста.", ephemeral=True)
        return
        
    with open("economy.json", "r") as f:
        data = json.load(f)
        
    user_data = data.get(guild_id, {}).get(user_id, {})
    businesses = user_data.get("businesses", [])
    
    if not businesses:
        await interaction.response.send_message("У вас пока нет ни одного бизнеса.")
        return
        
    embed = discord.Embed(title=f"Список бизнесов {interaction.user.display_name}", color=discord.Color.blue())
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    
    now = datetime.datetime.now()
    
    for i, biz in enumerate(businesses, 1):
        profit = BUSINESS_LEVELS[biz.get("level", 1)]["profit"]
        
        date_str = biz.get("last_collect") or biz.get("created_at")
        
        if isinstance(date_str, str):
            try:
                last_collect = datetime.datetime.fromisoformat(date_str)
            except:
                last_collect = now
        else:
            last_collect = now
            
        minutes_passed = (now - last_collect).total_seconds() / 60
        intervals = int(minutes_passed // 5)
        saved = intervals * profit
            
        embed.add_field(
            name=f"{i}. {biz['name']}",
            value=(
                f"Доход: {profit:,}$/5 мин\n"
                f"Накоплено: {saved:,}$\n"
                f"Создан: {last_collect.strftime('%d.%m.%Y %H:%M')}"
            ),
            inline=False
        )
        
    await interaction.response.send_message(embed=embed)

@business.command(name="delete", description="Удалить бизнес по номеру (из списка /business list)")
async def delete_biz(interaction: discord.Interaction, number: int):
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    
    with open("economy.json", "r") as f:
        data = json.load(f)
        
    user_data = data.get(guild_id, {}).get(user_id, {})
    businesses = user_data.get("businesses", [])
    
    if number < 1 or number > len(businesses):
        await interaction.response.send_message(f"❌ Бизнеса с номером {number} не существует. Проверьте список через `/business list`.", ephemeral=True)
        return
        
    removed_biz = businesses.pop(number - 1)
    
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await interaction.response.send_message(f"🗑️ Бизнес **«{removed_biz['name']}»** успешно удален!")



@business.command(name="rename", description="Переименовать бизнес")
async def rename_biz(interaction: discord.Interaction, number: int, new_name: str):
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    
    with open("economy.json", "r") as f:
        data = json.load(f)
        
    user_data = data.get(guild_id, {}).get(user_id, {})
    businesses = user_data.get("businesses", [])
    
    if number < 1 or number > len(businesses):
        await interaction.response.send_message(f"❌ Бизнеса с номером {number} не существует.", ephemeral=True)
        return
        
    old_name = businesses[number - 1]["name"]
    businesses[number - 1]["name"] = new_name
    
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await interaction.response.send_message(f"✏️ Бизнес «{old_name}» переименован в **«{new_name}»**!")

@business.command(name="help", description="Показать список доступных команд")
async def help_biz(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ Помощь по системе бизнеса", 
        description="Здесь список всех доступных команд:", 
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🛠 Основные команды:",
        value=(
            "**/business create** — Купить новый бизнес\n"
            "**/business list** — Посмотреть ваши бизнесы\n"
            "**/business delete <номер>** — Удалить бизнес\n"
            "**/business rename <номер> \"новое имя\"** — Переименовать"
        ),
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

if client.tree.get_command("business") is None:
    client.tree.add_command(business)

admin_group = app_commands.Group(name="a", description="Административные команды")

@admin_group.command(name="i", description="Выдать деньги пользователю (до 10 млрд)")
async def give_money(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ У вас недостаточно прав, чтобы использовать эту команду!", ephemeral=True)
        return

    if amount > 10000000000:
        await interaction.response.send_message("❌ Нельзя выдать больше 10 000 000 000 монет за раз!", ephemeral=True)
        return

    guild_id = str(interaction.guild_id)
    target_id = str(member.id)
    
    if not os.path.exists("economy.json"):
        with open("economy.json", "w") as f:
            json.dump({}, f)
            
    with open("economy.json", "r") as f:
        data = json.load(f)
        
    if guild_id not in data:
        data[guild_id] = {}
    if target_id not in data[guild_id]:
        data[guild_id][target_id] = {"balance": 0, "businesses": []}
        
    data[guild_id][target_id]["balance"] += amount
    
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)
        
    await interaction.response.send_message(f"✅ Успешно выдано **{amount:,}** монет пользователю {member.mention}.")

client.tree.add_command(admin_group)

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Экономика", value="eco", description="Бизнесы, работа, награды"),
            discord.SelectOption(label="Администрация", value="admin", description="Управление сервером"),
            discord.SelectOption(label="Модерация", value="mod", description="Наказания и очистка")
        ]
        super().__init__(placeholder="Выберите раздел...", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.blue())
        
        if self.values[0] == "eco":
            embed.title = "💰 Экономика"
            embed.description = (
                "/business create — Купить бизнес\n"
                "/business list — Список ваших бизнесов\n"
                "/business delete — Удалить бизнес\n"
                "/business rename — Переименовать\n"
                "/business collect — Собрать накопленное\n"
                "/work — Поработать\n"
                "/daily — Ежедневная награда\n"
                "/weekly — Еженедельная награда"
                "/deposit — Положить в банк\n"
                "/withdraw — Снять с банка\n"
                "/slots — Казино слоты\n"
                "/blacklack — Казино блекджек\n"
            )
        elif self.values[0] == "admin":
            embed.title = "🛠 Администрация"
            embed.description = (
                "/a i — Выдать деньги пользователю\n"
                "/warn — Выдать предупреждение\n"
                "/unwarn — Сняь предупреждение\n"
                "/warn_list — Список выданых предупреждений\n"
                "/business delete_player — Удаляет бизнесы игрока\n"
            )
        elif self.values[0] == "mod":
            embed.title = "🛡 Модерация"
            embed.description = (
                "/ban — Забанить участника\n"
                "/kick — Кикнуть участника\n"
                "/mute — Заглушить участника\n"
                "/unmute — Снять мут\n"
                "/unban — Разбаниь учасника\n"
            )
            
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

async def send_log(title, color, fields, message_id=None):
    log_channel = client.get_channel(LOG_CHANNEL_ID)
    if not log_channel: return
    embed = discord.Embed(title=title, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
    for name, value in fields.items():
        embed.add_field(name=name, value=value, inline=False)
    if message_id:
        embed.set_footer(text=f"ID сообщения: {message_id}")
    await log_channel.send(embed=embed)

@client.event
async def on_message_delete(message):
    if message.author.bot: return
    await send_log("Сообщение было удалено", discord.Color.from_rgb(231, 76, 60), {
        "Автор": f"{message.author.mention} ({message.author.name})",
        "Канал": message.channel.mention,
        "Текст": f"```\n{message.content or 'Нет текста'}\n```"
    }, message.id)

@client.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        await send_log("🛑 Пользователь забанен", discord.Color.red(), {
            "Нарушитель": user.mention,
            "Модератор": entry.user.mention,
            "Причина": entry.reason or "Не указана"
        })
        break

@client.event
async def on_member_unban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
        await send_log("✅ Пользователь разбанен", discord.Color.green(), {
            "Пользователь": user.mention,
            "Модератор": entry.user.mention
        })
        break

@client.event
async def on_member_remove(member):
    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target == member:
            await send_log("🥾 Участник кикнут", discord.Color.gold(), {
                "Участник": member.mention,
                "Модератор": entry.user.mention,
                "Причина": entry.reason or "Не указана"
            })
        break

@client.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
            if (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 5:
                moderator = entry.user
                added = [r for r in after.roles if r not in before.roles]
                removed = [r for r in before.roles if r not in after.roles]
                for role in added:
                    if role.id == MUTE_ROLE_ID:
                        await send_log("🤐 Пользователь замучен", discord.Color.dark_grey(), {"Участник": after.mention, "Модератор": moderator.mention, "Роль": role.name})
                for role in removed:
                    if role.id == MUTE_ROLE_ID:
                        await send_log("🔓 Пользователь размучен", discord.Color.green(), {"Участник": after.mention, "Модератор": moderator.mention, "Роль": role.name})
            break

@client.command(name="purge")
@commands.has_any_role("Персонал", "Старший персонал")
async def clear(ctx, amount: int):
    if amount < 1:
        await ctx.send("Укажите число больше 0")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    await send_log("Очистка сообщений", discord.Color.orange(), {
        "Модератор": ctx.author.mention,
        "Канал": ctx.channel.mention,
        "Удалено": f"{len(deleted)-1} сообщений"
    })

@client.command(name="log_ban")
@commands.has_permissions(ban_members=True)
async def log_ban(ctx, member: discord.Member, *, reason="Без причины"):
    await member.ban(reason=reason)
    await send_log("🔨 Бан участника", discord.Color.red(), {
        "Нарушитель": member.mention, "Модератор": ctx.author.mention, "Причина": reason
    })

@client.command(name="log_kick")
@commands.has_permissions(kick_members=True)
async def log_kick(ctx, member: discord.Member, *, reason="Без причины"):
    await member.kick(reason=reason)
    await send_log("👢 Кик участника", discord.Color.orange(), {
        "Нарушитель": member.mention, "Модератор": ctx.author.mention, "Причина": reason
    })

@client.command(name="log_unban")
@commands.has_permissions(ban_members=True)
async def log_unban(ctx, user_id: int):
    user = await client.fetch_user(user_id)
    await ctx.guild.unban(user)
    await send_log("🕊️ Разбан участника", discord.Color.green(), {
        "ID пользователя": user_id, "Модератор": ctx.author.mention
    })

@client.command(name="log_mute")
@commands.has_permissions(manage_roles=True)
async def log_mute(ctx, member: discord.Member, *, reason="Нарушение"):
    role = ctx.guild.get_role(MUTE_ROLE_ID)
    await member.add_roles(role, reason=reason)
    await send_log("🔇 Мут участника", discord.Color.dark_grey(), {
        "Нарушитель": member.mention, "Модератор": ctx.author.mention, "Причина": reason
    })

@client.command(name="log_unmute")
@commands.has_permissions(manage_roles=True)
async def log_unmute(ctx, member: discord.Member):
    role = ctx.guild.get_role(MUTE_ROLE_ID)
    await member.remove_roles(role)
    await send_log("🔊 Размут участника", discord.Color.blue(), {
        "Пользователь": member.mention, "Модератор": ctx.author.mention
    })

@client.command(name="log_warn")
@commands.has_permissions(manage_roles=True)
async def log_warn(ctx, member: discord.Member, *, reason="Нарушение"):
    await send_log("⚠️ Выдан варн", discord.Color.gold(), {
        "Нарушитель": member.mention, "Модератор": ctx.author.mention, "Причина": reason
    })

user_data = {}
total_limit_roles_1_given = 0
MAX_LIMIT_1_ROLES = 10

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"money": 0, "cases": {"common": 0, "summer": 0}, "has_role": False}
    return user_data[uid]

@client.group(name="case", invoke_without_command=True)
async def case(ctx):
    await ctx.send("Используй: !case info <название>, !case inventory, или !case open <id>")

@case.command(name="info")
async def info(ctx, name: str):
    emb = discord.Embed(title=f"Информация: {name}", color=discord.Color.blue())
    emb.add_field(name="Возможный дроп:", value="💰 Деньги - от 100,000 до 1,000,000\n📦 Летние кейсы\n👑 Лимитированная роль (1%)", inline=False)
    emb.set_footer(text="彡★❄️★彡")
    await ctx.send(embed=emb)

@case.command(name="inventory")
async def case_inventory(ctx):
    file_path = "economy.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    
    user_data = data.get(guild_id, {}).get(user_id, {})
    cases = user_data.get("cases", {})
    balance = user_data.get("balance", 0)
    
    emb = discord.Embed(title=f"🎒 Инвентарь {ctx.author.name}", color=discord.Color.blue())
    
    case_names = {
        "caseception": "Caseception",
        "money_case": "Money Case",
        "loot_stash": "Loot Stash",
        "common": "Common Case",
        "summer": "Summer Case"
    }
    
    cases_text = ""
    for key, name in case_names.items():
        count = cases.get(key, 0)
        if count > 0:
            cases_text += f"• **{name}**: {count} шт.\n"
    
    if not cases_text:
        cases_text = "Кейсов нет.\n"
        
    roles_text = ""
    if user_data.get("has_role"): roles_text += "• ⋆˚ sᴜᴍᴍᴇʀLune ⋆˚ (!title use summer)\n"
    if user_data.get("has_custom_role"): roles_text += "• ✨ Кастомная роль (!title use custom)\n"
    if user_data.get("has_role_2"): roles_text += "• 👑 Лимитированная роль 2 (!title use limit2)\n"
    
    emb.add_field(name="📦 Кейсы:", value=cases_text, inline=False)
    
    if roles_text:
        emb.add_field(name="👑 Полученные роли:", value=roles_text, inline=False)
        
    emb.add_field(name="💰 Баланс:", value=f"{balance:,}$", inline=False)
    
    await ctx.send(embed=emb)

MAX_LIMIT_ROLES = 100
LIMIT_ROLE_2_MAX = 10

total_limit_roles_given = 0
total_limit_roles_2_given = 0

def get_user(user_id):
    if not os.path.exists("economy.json"):
        with open("economy.json", "w") as f: json.dump({}, f)
    with open("economy.json", "r") as f:
        data = json.load(f)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"money": 100000000, "cases": {}}
        with open("economy.json", "w") as f: json.dump(data, f, indent=4)
    return data[uid]

def save_user(user_id, user_data):
    with open("economy.json", "r") as f:
        all_data = json.load(f)
    all_data[str(user_id)] = user_data
    with open("economy.json", "w") as f:
        json.dump(all_data, f, indent=4)

@case.command(name="open")
async def open_case(ctx, case_id: str):
    global total_limit_roles_given, total_limit_roles_2_given
    file_path = "economy.json"
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data or user_id not in data[guild_id]:
        await ctx.send("❌ Профиль не найден!")
        return

    user_data = data[guild_id][user_id]
    
    if user_data.get("cases", {}).get(case_id, 0) <= 0:
        await ctx.send("❌ У тебя нет такого кейса!")
        return

    user_data["cases"][case_id] -= 1
    roll = random.random()
    drop_text = ""

    if case_id == "caseception":
        sub_roll = random.random()
        if sub_roll < 0.25:
            q = 3 if roll < 0.15 else (2 if roll < 0.50 else 1)
            user_data["cases"]["loot_stash"] = user_data["cases"].get("loot_stash", 0) + q
            drop_text = f"📦 {q} шт. Loot Stash"
        elif sub_roll < 0.50:
            q = 3 if roll < 0.45 else (2 if roll < 0.65 else 1)
            user_data["cases"]["common"] = user_data["cases"].get("common", 0) + q
            drop_text = f"📦 {q} шт. Common Case"
        elif sub_roll < 0.75:
            q = 3 if roll < 0.10 else (2 if roll < 0.25 else 1)
            user_data["cases"]["summer"] = user_data["cases"].get("summer", 0) + q
            drop_text = f"📦 {q} шт. Summer Case"
        else:
            amt = random.choice([100000, 500000, 1000000])
            user_data["balance"] += amt
            drop_text = f"💸 {amt:,}$"
    elif case_id == "money_case":
        amt = 1000000 if roll < 0.20 else (500000 if roll < 0.45 else (300000 if roll < 0.60 else (200000 if roll < 0.70 else 100000)))
        user_data["balance"] += amt
        drop_text = f"💸 {amt:,}$"
    elif case_id == "loot_stash":
        if roll < 0.05:
            if total_limit_roles_given < MAX_LIMIT_ROLES:
                user_data["has_role"] = True
                total_limit_roles_given += 1
                drop_text = f"👑 Лимитированная роль ({total_limit_roles_given}/{MAX_LIMIT_ROLES})"
            else:
                user_data["balance"] += 1000000
                drop_text = "💸 Лимит ролей исчерпан! Бонус 1,000,000$"
        elif roll < 0.15:
            user_data["has_custom_role"] = True
            drop_text = "✨ Кастомная роль"
        else:
            amt = random.choice([250000, 750000])
            user_data["balance"] += amt
            drop_text = f"💸 {amt:,}$"
    elif case_id == "common":
        if roll < 0.25:
            user_data["cases"]["summer"] = user_data["cases"].get("summer", 0) + 1
            drop_text = "📦 1 Summer Case"
        else:
            user_data["balance"] += 500000
            drop_text = "💸 500,000$"
    elif case_id == "summer":
        if roll < 0.01:
            if total_limit_roles_2_given < LIMIT_ROLE_2_MAX:
                user_data["has_role_2"] = True
                total_limit_roles_2_given += 1
                drop_text = "👑 Лимитированная роль (используй !title use)"
            else:
                amount = 1000000
                user_data["balance"] += amount
                drop_text = f"💸 Роль закончилась! Вам начислено {amount:,}$ бонусом"
        else:
            amount = random.choice([100000, 250000, 500000, 800000, 1000000])
            user_data["balance"] += amount
            drop_text = f"💸 {amount:,}$"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    emb = discord.Embed(title=f"Поздравляем! Ваш дроп за открытие {case_id} 💼:", color=discord.Color.green())
    emb.description = f"• Открытие кейсов пользователя {ctx.author.name}\n\n• {drop_text}"
    emb.add_field(name="💰 Текущий баланс", value=f"{user_data['balance']:,}$", inline=False)
    emb.set_footer(text=f"彡★❄️★彡 | R1: {total_limit_roles_given}/{MAX_LIMIT_ROLES} | R2: {total_limit_roles_2_given}/{LIMIT_ROLE_2_MAX}")
    await ctx.send(embed=emb)

@case.group(name="title", invoke_without_command=True)
async def title(ctx):
    await ctx.send("Используй: !title info или !title use <тип>")

@title.command(name="info")
async def title_info(ctx):
    emb = discord.Embed(title="📜 Список доступных ролей", color=discord.Color.gold())
    emb.add_field(name="⋆˚ sᴜᴍᴍᴇʀLune ⋆˚", value="Способ получения: Выпадение из кейса (SummerCase).", inline=False)
    emb.add_field(name="✨ Кастомная роль", value="Способ получения: Loot Stash", inline=False)
    emb.add_field(name="👑 Лимитированная роль 2", value="Способ получения: Summer Case", inline=False)
    emb.set_footer(text="彡★❄️★彡")
    await ctx.send(embed=emb)

@title.command(name="use")
async def title_use(ctx, role_type: str = None):
    if not role_type:
        return await ctx.send("❌ Укажите тип роли: summer, custom или limit2")

    file_path = "economy.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    user_data = data.get(guild_id, {}).get(user_id, {})
    if not user_data:
        return await ctx.send("❌ Профиль не найден!")

    roles_config = {
        "summer": {"key": "has_role", "id": ROLE_SUMMER_LIMIT_ID, "name": "⋆˚ sᴜᴍᴍᴇʀLune ⋆˚"},
        "custom": {"key": "has_custom_role", "id": ROLE_CUSTOM_ID, "name": "Кастомная роль"},
        "limit2": {"key": "has_role_2", "id": ROLE_LOOT_STASH_LIMIT_ID, "name": "Лимитированная роль 2"}
    }

    if role_type not in roles_config:
        return await ctx.send("❌ Неверный тип! Используй: summer, custom или limit2")

    cfg = roles_config[role_type]
    
    if user_data.get(cfg["key"], False):
        role = ctx.guild.get_role(cfg["id"])
        if role:
            await ctx.author.add_roles(role)
            await ctx.send(f"✅ {cfg['name']} успешно надета!")
        else:
            await ctx.send("❌ Ошибка: роль не найдена на сервере (проверь ID).")
    else:
        await ctx.send("❌ У тебя нет доступа к этой роли!")

user_data = {}
SUNSET_ROLE_ID = 1515130377394458644

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"money": 0, "sunset_cooldown": 0}
    return user_data[uid]

@client.command(name="sunset")
async def sunset(ctx):
    file_path = "economy.json"
    with open(file_path, "r") as f:
        data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data: data[guild_id] = {}
    if user_id not in data[guild_id]: data[guild_id][user_id] = {"balance": 0, "bank": 0, "cases": {}, "sunset_cooldown": 0}
    
    user_data = data[guild_id][user_id]
    
    if SUNSET_ROLE_ID not in [r.id for r in ctx.author.roles]:
        await ctx.send("❌ У вас нет роли ⋆˚ sᴜᴍᴍᴇʀLune ⋆˚!")
        return
        
    current_time = time.time()
    last_use = user_data.get("sunset_cooldown", 0)
    
    if current_time - last_use < 900:
        remaining = int(900 - (current_time - last_use))
        await ctx.send(f"Вы сможете использовать эту команду через {remaining // 60} минут и {remaining % 60} секунд.")
        return
        
    user_data["balance"] += 3000000
    user_data["sunset_cooldown"] = current_time
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    
    emb = discord.Embed(title="Sunset Bonus", color=discord.Color.dark_grey())
    emb.description = f"{ctx.author.mention} только что активировал Sunset и получил **3,000,000$**."
    await ctx.send(embed=emb)

user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"money": 0, "cases": {"common": 0}, "has_role": False}
    return user_data[uid]

@client.group(name="shop", invoke_without_command=True)
async def shop(ctx):
    embed = discord.Embed(title="🛒 Магазин", color=discord.Color.purple())
    embed.add_field(name="Common case", value="Цена: 1,000,000\nКоманда: !shop buy common <кол-во>", inline=False)
    embed.add_field(name="Loot Stash", value="Цена: 10,000,000\nКоманда: !shop buy loot_stash <кол-во>", inline=False)
    embed.set_footer(text="Владельцам роли ⋆˚ sᴜᴍᴍᴇʀLune ⋆˚ скидка 25%!")
    await ctx.send(embed=embed)

@shop.command(name="buy")
async def shop_buy(ctx, case_name: str, amount: int = 1):
    file_path = "economy.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data: data[guild_id] = {}
    if user_id not in data[guild_id]: 
        data[guild_id][user_id] = {"balance": 0, "bank": 0, "cases": {}}
    
    user_data = data[guild_id][user_id]
    if "cases" not in user_data: user_data["cases"] = {}
    
    prices = {
        "common": 1000000, 
        "summer": 2000000,
        "loot_stash": 10000000
    }
    
    if case_name not in prices:
        await ctx.send(f"❌ Доступны: {', '.join(prices.keys())}")
        return

    price = prices[case_name]
    
    if ROLE_SUMMER_LIMIT_ID in [r.id for r in ctx.author.roles]:
        price = int(price * 0.75)
        
    total_cost = price * amount
    
    if user_data.get("balance", 0) >= total_cost:
        user_data["balance"] -= total_cost
        user_data["cases"][case_name] = user_data["cases"].get(case_name, 0) + amount
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        await ctx.send(f"✅ Куплено {amount} шт. {case_name} за {total_cost:,}$!")
        
        inventory_cmd = ctx.bot.get_command("case").get_command("inventory")
        if inventory_cmd:
            await ctx.invoke(inventory_cmd)
            
    else:
        await ctx.send(f"❌ Недостаточно средств! Нужно: {total_cost:,}$")

@client.command(name="free")
async def free_case(ctx):
    file_path = "economy.json"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    if guild_id not in data: data[guild_id] = {}
    if user_id not in data[guild_id]: 
        data[guild_id][user_id] = {"balance": 0, "cases": {}, "last_free_claim": "2000-01-01"}

    user_data = data[guild_id][user_id]
    last_claim_str = user_data.get("last_free_claim", "2000-01-01")
    last_claim = datetime.datetime.fromisoformat(last_claim_str)
    now = datetime.datetime.now()

    if (now - last_claim).total_seconds() < 86400:
        hours_left = 24 - int((now - last_claim).total_seconds() // 3600)
        await ctx.send(f"❌ Ты уже забирал кейсы! Можно будет забрать через {hours_left} ч.")
        return

    cases = user_data.get("cases", {})
    cases["common"] = cases.get("common", 0) + 3
    cases["summer"] = cases.get("summer", 0) + 3
    user_data["cases"] = cases
    
    user_data["last_free_claim"] = now.isoformat()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    await ctx.send("🎁 Ты успешно получил 3 Common Case и 3 Summer Case! Следующий раз можно забрать через 24 часа.")

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"money": 0, "cases": {"1_summer": 0, "2_summer": 0, "3_summer": 0, "common": 0}, "has_role": False}
    return user_data[uid]

@client.group(name="own")
async def own(ctx):
    pass

@own.group(name="i")
async def i(ctx):
    pass

@i.command(name="case")
@commands.has_role("Scarletᵒʷⁿᵉʳ")
async def i_case(ctx, case_name: str, amount: int, member: discord.Member):
    file_path = "economy.json"
    
    with open(file_path, "r") as f:
        data = json.load(f)

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id not in data: 
        data[guild_id] = {}
    if user_id not in data[guild_id]: 
        data[guild_id][user_id] = {"balance": 0, "bank": 0, "cases": {}}
    
    if "cases" not in data[guild_id][user_id]: 
        data[guild_id][user_id]["cases"] = {}

    data[guild_id][user_id]["cases"][case_name] = data[guild_id][user_id]["cases"].get(case_name, 0) + amount

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    await ctx.send(f"✅ Выдано {amount} шт. {case_name} пользователю {member.mention}")

@i_case.error
async def i_case_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ У тебя нет прав Owner!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Участник не найден!")

class ApplicationModal(discord.ui.Modal):
    def __init__(self, position):
        super().__init__(title=f"Заявка: {position}")
        self.position = position
        
        self.add_item(discord.ui.TextInput(label="Имя и возраст", placeholder="Иван, 16 лет", style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Сколько времени готовы уделять?", placeholder="3-4 часа в день", style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Творческая оценка", placeholder="Оцените свои навыки...", style=discord.TextStyle.paragraph))
        self.add_item(discord.ui.TextInput(label="Опыт работы", placeholder="Был на таких-то проектах...", style=discord.TextStyle.paragraph))
        self.add_item(discord.ui.TextInput(label="Что выделяет вас?", placeholder="Расскажите о себе", style=discord.TextStyle.paragraph, max_length=4000))

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Анкеты")
        if not category:
            category = await guild.create_category("Анкеты")
        
        curator = discord.utils.get(guild.roles, name="Curator")
        manager = discord.utils.get(guild.roles, name="Staff Manager")
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        if curator:
            overwrites[curator] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if manager:
            overwrites[manager] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        ticket_channel = await guild.create_text_channel(f"заявка-{interaction.user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(title=f"Новая заявка на должность: {self.position}", color=discord.Color.blue())
        for item in self.children:
            embed.add_field(name=item.label, value=item.value, inline=False)
        
        role_mentions = f"{curator.mention if curator else '<@&1501306966427959406>'} {manager.mention if manager else '<@&1510623453785358406>'}"
        await ticket_channel.send(
            content=f"{role_mentions}, рассмотрите заявку!", 
            embed=embed
        )
        
        await interaction.response.send_message(f"✅ Ваша заявка отправлена в {ticket_channel.mention}", ephemeral=True)
        
class PositionSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moderator", value="Moderator", emoji="🔵"),
            discord.SelectOption(label="Eventer", value="Eventer", emoji="🟣"),
            discord.SelectOption(label="Support", value="Support", emoji="🟡"),
        ]
        super().__init__(placeholder="Выберите должность...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ApplicationModal(self.values[0]))

class QuestionnaireView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PositionSelect())

@client.command()
async def ticket(ctx, action=None):
    if action != "close":
        return 

    curator_role = discord.utils.get(ctx.guild.roles, name="Curator")
    manager_role = discord.utils.get(ctx.guild.roles, name="Staff Manager")
    
    is_authorized = ctx.author.guild_permissions.administrator
    if (curator_role and curator_role in ctx.author.roles) or (manager_role and manager_role in ctx.author.roles):
        is_authorized = True

    is_ticket_channel = ctx.channel.category and ctx.channel.category.name == "Анкеты"
    
    if not is_ticket_channel:
        await ctx.send("❌ Эту команду можно использовать только в каналах с заявками!")
        return

    if is_authorized:
        await ctx.send("⚠️ Канал будет удален через 5 секунд...")
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("❌ У вас нет прав для закрытия заявки!")

@client.event
async def on_ready():
    client.add_view(QuestionnaireView())
    target_channel = client.get_channel(1505855219786055782)
    if target_channel:
        async for message in target_channel.history(limit=5):
            if message.author == client.user and message.components:
                return
        
        embed = discord.Embed(
            title="💼 Вакансии",
            description="**# ・Вакансии**\n\n"
                        "Мы очень нуждаемся в рабочих лапках, если у тебя есть достаточно свободного времени и хочешь сделать вклад в развитие проекта — можешь смело оставить свою заявку!\n\n"
                        "・ <@&1500175396904243434> - Модерирует сервер\n\n"
                        "・ <@&1500943411371442277> - Проводит ивенты и розыгрыши\n\n"
                        "・ <@&1500942938719522970> - Помогает участникам по серверу",
            color=discord.Color.red()
        )
        await target_channel.send(embed=embed, view=QuestionnaireView())

@client.command()
@commands.has_permissions(administrator=True)
async def setup_apply(ctx):
    embed = discord.Embed(
        title="💼 Вакансии",
        description="**# ・Вакансии**\n\n"
                    "Мы очень нуждаемся в рабочих лапках, если у тебя есть достаточно свободного времени и хочешь сделать вклад в развитие проекта — можешь смело оставить свою заявку!\n\n"
                    "・ <@&1500175396904243434> - Модерирует сервер\n\n"
                    "・ <@&1500943411371442277> - Проводит ивенты и розыгрыши\n\n"
                    "・ <@&1500942938719522970> - Помогает участникам по серверу",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, view=QuestionnaireView())



ZERO_GIFS = [
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542980597184593940/bc11809c97271e15b7495b7ccd880ab7_1.gif?ex=6a93dce9&is=6a928b69&hm=e76eab60756985cb087eb8a52478c8fdd09f4f469a0a1292ea6d11b3b95b2b84&",
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542980621318750208/5583320e11154c207f54711a927e9526.gif?ex=6a93dcef&is=6a928b6f&hm=06a0c93492cc8cee69da149329a832592a17863314b78534c09ba8c2eae263c3&",
    "httаps://cdn.discordapp.com/attachments/1505813045249708144/1542980780853297202/4db3008dea23de3f36b1d588b0f5f4df.gif?ex=6a93dd15&is=6a928b95&hm=394cd136b0d46c4c1534beb9aab984834e6d583cdce61e5c18ae6518690dd52c&",
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542980798641213553/cef569820773b0f5d54ee34cfa18e1f8.gif?ex=6a93dd19&is=6a928b99&hm=3e5fca11fc11468ef80660854d1e035ce6c6533817d81e81f16078ee0113e6db&",
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542981001817493626/zero-two.gif?ex=6a93dd4a&is=6a928bca&hm=f6f3760ba67da49f05b8890788887d3e808081f812c50f6b70806de9d57c0737&",
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542981252137623582/8677b01b4e5837808a3d4eae3d878557.gif?ex=6a93dd85&is=6a928c05&hm=2951bcb4fb9c8cc76c884c48805f998e9040958a0567dd0147c92e4c57ecbb53&",
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542981405594624100/bcc5acf6915f9da95b7c0641745a3a66.gif?ex=6a93ddaa&is=6a928c2a&hm=e76b43525cf90858051b6f550e23c2932e07a600bd43c32909dd1443e920b36e&",
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542981455964143738/071a36c7a48767b3a56465d712525a7a.gif?ex=6a93ddb6&is=6a928c36&hm=2eace3ccbc180601ad00f069b775c7a258d3ed44a22a69f8e8b4a3d60936c804&",
    "https://cdn.discordapp.com/attachments/1505813045249708144/1542981508032110715/b4ddf4655b1cabc998d8efbc15fd7039.gif?ex=6a93ddc2&is=6a928c42&hm=3548c93980b7a622e9c882666997df8e9d21b2e2f146ce161aba71aea5803a77&"
]

PHRASES = [
    "«Ты ведь не сбежишь от меня, да?..»",
    "«Я чувствую твой пульс даже отсюда»",
    "«Сладкий... ты опять смотрел на других?»",
    "«Если ты умрёшь — я убью тебя сама»",
    "«Помнишь тот день? Я помню всё»",
    "«Ты — мой кусочек счастья... не потеряйся»",
    "«Давай сбежим? Туда, где нет ни FRANXX, ни войны»",
    "«...Ты тоже видишь этот сон?»",
    "«Ты тоже ищешь меня в каждой жизни?»"
]

zero_data = {}

async def restore_nickname(member: discord.Member, original_nick: str, delay: int = 900):
    await asyncio.sleep(delay)
    try:
        await member.edit(nick=original_nick)
    except discord.Forbidden:
        pass

async def remove_eternal_role(member: discord.Member, role: discord.Role, delay: int = 3600):
    await asyncio.sleep(delay)
    try:
        await member.remove_roles(role)
    except discord.Forbidden:
        pass

@client.command(name="zero")
@commands.has_role(ROLE_ZERO_TWO_WIFE_ID)
async def zero(ctx, *, sub_command: str = None):
    user_id = ctx.author.id
    now = time.time()

    if user_id not in zero_data:
        zero_data[user_id] = {
            "cooldown": 0,
            "penalty": 0,
            "streak": 0,
            "last_used": 0,
            "original_nick": ctx.author.display_name,
            "current_index": 0  # С какого номера начинать (0 — первая фраза)
        }

    udata = zero_data[user_id]

    if sub_command and sub_command.strip().lower() == "молчать":
        udata["penalty"] = now + 300
        udata["streak"] = 0
        emb = discord.Embed(
            title="💔 Zero Two обиделась...",
            description=f"{ctx.author.mention}, хмф! Раз так — я с тобой не разговариваю **5 минут**!",
            color=discord.Color.from_rgb(139, 0, 0)
        )
        emb.set_image(url=ZERO_GIFS[0])
        await ctx.send(embed=emb)
        return

    if now < udata["penalty"]:
        left = int(udata["penalty"] - now)
        mins, secs = divmod(left, 60)
        emb = discord.Embed(
            title="🤐 Зеро Два отвернулась",
            description=f"{ctx.author.mention}, она всё еще молчит... Подожди `{mins}мин {secs}сек`.",
            color=discord.Color.dark_gray()
        )
        await ctx.send(embed=emb)
        return
    
    if now < udata["cooldown"]:
        left = int(udata["cooldown"] - now)
        emb = discord.Embed(
            title="⏳ Не так быстро, Любимый!",
            description=f"Zero Two переводит дыхание. Подожди еще `{left}` сек.",
            color=discord.Color.gold()
        )
        await ctx.send(embed=emb)
        return
    
    if now - udata["last_used"] <= 60:
        udata["streak"] += 1
    else:
        udata["streak"] = 1

    udata["cooldown"] = now + 30
    udata["last_used"] = now

    if udata["streak"] == 5:
        udata["streak"] = 0
        emb = discord.Embed(
            title="✨ Секретное откровение ✨",
            description=f"{ctx.author.mention}\n\n*«Ты тоже ищешь меня в каждой жизни?»*",
            color=discord.Color.purple()
        )
        emb.set_image(url=ZERO_GIFS[0])

        role = discord.utils.get(ctx.guild.roles, name="Вечные")
        if not role:
            try:
                role = await ctx.guild.create_role(name="Вечные", color=discord.Color.purple())
            except discord.Forbidden:
                role = None

        if role:
            try:
                await ctx.author.add_roles(role)
                emb.set_footer(text="Тебе выдана секретная роль «Вечные» на 1 час!")
                asyncio.create_task(remove_eternal_role(ctx.author, role, 3600))
            except discord.Forbidden:
                emb.set_footer(text="У бота нет прав для выдачи роли.")

        await ctx.send(embed=emb)
        return
    
    index = udata["current_index"]
    chosen_text = PHRASES[index]
    chosen_gif = ZERO_GIFS[index]
    user_name = ctx.author.name

    udata["current_index"] = (index + 1) % len(PHRASES)

    color = discord.Color.from_rgb(255, 182, 193)
    new_nick = f"Её пилот {user_name}"

    try:
        await ctx.author.edit(nick=new_nick[:32])
        asyncio.create_task(restore_nickname(ctx.author, udata["original_nick"], 900))
    except discord.Forbidden:
        pass

    emb = discord.Embed(
        title="🌸 Zero Two",
        description=f"{ctx.author.mention}\n\n**{chosen_text}**",
        color=color
    )
    emb.set_image(url=chosen_gif)
    emb.set_footer(text=f"Фраза {index + 1}/8 | Прогресс серии: {udata['streak']}/5 | Кулдаун 30с")
    
    await ctx.send(embed=emb)

@zero.error
async def zero_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        emb = discord.Embed(
            title="⛔ Доступ ограничен",
            description=f"{ctx.author.mention}, эту команду могут использовать только обладатели роли **Zero-two wife💘**!",
            color=discord.Color.red()
        )
        await ctx.send(embed=emb)

KISS_GIFS = [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]

SLAP_GIFS = [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]

SEX_GIFS = [
    "h1ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247862043775136/OPHr.gif?ex=6a942d12&is=6a92db92&hm=5b62f72165fc9a17ecb662acb68784c47d8665d54670b2d208c64ee11b717039&",
    "h2ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247862752747520/rfyr2.gif?ex=6a942d12&is=6a92db92&hm=ec7d32a14208d439e6fa7a040d9023f52c358d73e15355340d52c8a2021169a3&",
    "h3ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247863382020136/06cd557d.gif?ex=6a942d12&is=6a92db92&hm=a7bf5761a88689946ad7651b6b86622400865d30634da00c77748c39ade30833&",
    "h4ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247863906173008/1Zgu.gif?ex=6a942d12&is=6a92db92&hm=7b3c7f1de61b3599d38c944581ee33c3759eadcf7be5f1b75bebf1bbfddc553f&",
    "h5ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247864954880120/6xh4.gif?ex=6a942d13&is=6a92db93&hm=644396b300db64aabdbdac3cb97744c46f6289d86d39dc2269601384601201a1&",
    "h6ttps://cdn.discordapp.com/attachments/1543244547453358101/1543248024728379422/ai-chan-in-her-waitress-uniform-s1e4-e9-ova2-v0-wzafzyh40hub1.gif?ex=6a942d39&is=6a92dbb9&hm=0d7bf022251e41f398fa0d25c683dfa8d116df40c4e102f2a3c3f2735431b737&",
    "h7ttps://cdn.discordapp.com/attachments/1543244547453358101/1543248025072435280/anime-love-23.gif?ex=6a942d39&is=6a92dbb9&hm=d021795b09b714361e51f3df2dc470b3b27f0d2441bbaa473a91a154fa9372be&",
    "h8ttps://cdn.discordapp.com/attachments/1543244547453358101/1543248053777997845/tumblr_n6gbzqv4VX1so56pco2_500.gif?ex=6a942d40&is=6a92dbc0&hm=e73c8b2d5bd2c94396cb7d3648eb5a720c568ae08dac688f4c7a36900afdb62a&",
    "",
    ""
]

MARRY_KISS_GIFS = [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]

MARRY_SEX_GIFS = [
    "h1ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247862043775136/OPHr.gif?ex=6a942d12&is=6a92db92&hm=5b62f72165fc9a17ecb662acb68784c47d8665d54670b2d208c64ee11b717039&",
    "h2ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247862752747520/rfyr2.gif?ex=6a942d12&is=6a92db92&hm=ec7d32a14208d439e6fa7a040d9023f52c358d73e15355340d52c8a2021169a3&",
    "h3ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247863382020136/06cd557d.gif?ex=6a942d12&is=6a92db92&hm=a7bf5761a88689946ad7651b6b86622400865d30634da00c77748c39ade30833&",
    "h4ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247863906173008/1Zgu.gif?ex=6a942d12&is=6a92db92&hm=7b3c7f1de61b3599d38c944581ee33c3759eadcf7be5f1b75bebf1bbfddc553f&",
    "h5ttps://cdn.discordapp.com/attachments/1543244547453358101/1543247864954880120/6xh4.gif?ex=6a942d13&is=6a92db93&hm=644396b300db64aabdbdac3cb97744c46f6289d86d39dc2269601384601201a1&",
    "h6ttps://cdn.discordapp.com/attachments/1543244547453358101/1543248024728379422/ai-chan-in-her-waitress-uniform-s1e4-e9-ova2-v0-wzafzyh40hub1.gif?ex=6a942d39&is=6a92dbb9&hm=0d7bf022251e41f398fa0d25c683dfa8d116df40c4e102f2a3c3f2735431b737&",
    "h7ttps://cdn.discordapp.com/attachments/1543244547453358101/1543248025072435280/anime-love-23.gif?ex=6a942d39&is=6a92dbb9&hm=d021795b09b714361e51f3df2dc470b3b27f0d2441bbaa473a91a154fa9372be&",
    "h8ttps://cdn.discordapp.com/attachments/1543244547453358101/1543248053777997845/tumblr_n6gbzqv4VX1so56pco2_500.gif?ex=6a942d40&is=6a92dbc0&hm=e73c8b2d5bd2c94396cb7d3648eb5a720c568ae08dac688f4c7a36900afdb62a&",
    "",
    ""
]

MARRY_SLAP_GIFS = [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]

@client.command(name="kiss")
async def kiss_cmd(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send(f"{ctx.author.mention}, целуйся с кем-нибудь другим ❤️")
        return
    emb = discord.Embed(description=f"{ctx.author.mention} поцеловал {member.mention}", color=discord.Color.pink())
    emb.set_image(url=random.choice(KISS_GIFS))
    await ctx.send(embed=emb)


@client.command(name="slap")
async def slap_cmd(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send(f"{ctx.author.mention} дал сам себе пощечину. Больно же!")
        return
    emb = discord.Embed(description=f"{ctx.author.mention} дал пощечину {member.mention} 💢", color=discord.Color.red())
    emb.set_image(url=random.choice(SLAP_GIFS))
    await ctx.send(embed=emb)


@client.command(name="sex")
async def sex_cmd(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send(f"{ctx.author.mention}, с самим собой нельзя!")
        return
    emb = discord.Embed(description=f"{ctx.author.mention} трахнул {member.mention}", color=discord.Color.purple())
    emb.set_image(url=random.choice(SEX_GIFS))
    await ctx.send(embed=emb)

@client.group(name="marry", invoke_without_command=True)
async def marry(ctx):
    await ctx.send(f"{ctx.author.mention}, используй: `!marry menu`, `!marry propose @user`, `!marry accept`, `!marry deny`, `!marry divorce`, `!marry level up`, `!marry level info`, `!marry child guardianship @user`")

pending_proposals = {}
divorce_requests = {}
user_cooldowns = {}

MARRY_FILE = "marry.json"

def load_marry_data():
    if not os.path.exists(MARRY_FILE):
        return {}
    try:
        with open(MARRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_marry_data(data):
    with open(MARRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_marriage_cooldown(user_id, action_type):
    now = time.time()
    key = f"{user_id}_{action_type}"
    last_time = user_cooldowns.get(key, 0)
    if now - last_time < 600:  # 10 минут
        return int(600 - (now - last_time))
    user_cooldowns[key] = now
    return 0

@marry.command(name="menu")
async def marry_menu(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = load_marry_data()
    user_id = str(target.id)

    if user_id not in data or not data[user_id].get("spouse"):
        await ctx.send(f"У {target.mention} нет второй половинки.")
        return

    spouse_id = data[user_id]["spouse"]
    spouse_member = ctx.guild.get_member(int(spouse_id))
    spouse_name = spouse_member.name if spouse_member else "Партнер"
    target_name = target.name

    spouse_obj = data[user_id]
    level = spouse_obj.get("level", 1)
    points = spouse_obj.get("love_points", 0)
    date = spouse_obj.get("date", "Неизвестно")
    child_id = spouse_obj.get("child")

    child_member = ctx.guild.get_member(int(child_id)) if child_id else None
    child_text = child_member.mention if child_member else "Детей пока нет."

    needed_points = LEVEL_REQUIREMENTS.get(level, 50)
    progress_in_level = min(points, needed_points)
    
    filled_hearts = min(10, int((progress_in_level / needed_points) * 10)) if needed_points > 0 else 10
    empty_hearts = 10 - filled_hearts
    bar = "❤️" * filled_hearts + "🤍" * empty_hearts

    emb = discord.Embed(
        description=(
            f"❤️ **Семейный союз:**\n"
            f"**{target_name} & {spouse_name}**\n\n"
            f"Прогресс до {level + 1} уровня:\n"
            f"{bar}\n"
            f"({points}/{needed_points})\n\n"
            f"💍 Партнер 1\n"
            f"{target.mention} ♀️\n\n"
            f"💍 Партнер 2\n"
            f"{spouse_member.mention if spouse_member else '<@' + spouse_id + '>'} ♂️\n\n"
            f"📈 Уровень\n"
            f"{level}\n\n"
            f"❤️ Очки Любви\n"
            f"{points}\n\n"
            f"📅 Дата Свадьбы\n"
            f"{date}\n\n"
            f"👥 Дети\n"
            f"{child_text}"
        ),
        color=discord.Color.from_rgb(255, 105, 180)
    )
    emb.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=emb)

@marry.command(name="kiss")
async def marry_kiss(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send(f"{ctx.author.mention}, целуйся с кем-нибудь другим ❤️")
        return

    left = check_marriage_cooldown(ctx.author.id, "kiss")
    if left > 0:
        mins, secs = divmod(left, 60)
        await ctx.send(f"⏳ Подожди еще `{mins} мин {secs} сек` перед следующим семейным поцелуем.")
        return

    data = load_marry_data()
    author_id = str(ctx.author.id)
    target_id = str(member.id)

    is_married = (author_id in data and data[author_id].get("spouse") == target_id)

    desc = f"{ctx.author.mention} поцеловал {member.mention}"
    if is_married:
        data[author_id]["love_points"] = data[author_id].get("love_points", 0) + 1
        data[target_id]["love_points"] = data[target_id].get("love_points", 0) + 1
        save_marry_data(data)
        desc += "\n+ 1 очко любви ❤️"
    else:
        desc += "\n*(Очко любви не засчитано, так как вы не состоите в браке)*"

    emb = discord.Embed(description=desc, color=discord.Color.pink())
    emb.set_image(url=random.choice(MARRY_KISS_GIFS))
    await ctx.send(embed=emb)


@marry.command(name="sex")
async def marry_sex(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send(f"{ctx.author.mention}, с самим собой нельзя!")
        return

    left = check_marriage_cooldown(ctx.author.id, "sex")
    if left > 0:
        mins, secs = divmod(left, 60)
        await ctx.send(f"⏳ Подожди еще `{mins} мин {secs} сек` перед следующим разом.")
        return

    data = load_marry_data()
    author_id = str(ctx.author.id)
    target_id = str(member.id)

    is_married = (author_id in data and data[author_id].get("spouse") == target_id)

    desc = f"{ctx.author.mention} трахнул {member.mention}"
    if is_married:
        data[author_id]["love_points"] = data[author_id].get("love_points", 0) + 1
        data[target_id]["love_points"] = data[target_id].get("love_points", 0) + 1
        save_marry_data(data)
        desc += "\n+ 1 очко любви ❤️"
    else:
        desc += "\n*(Очко любви не засчитано, так как вы не состоите в браке друг с другом)*"

    emb = discord.Embed(description=desc, color=discord.Color.purple())
    emb.set_image(url=random.choice(MARRY_SEX_GIFS))
    await ctx.send(embed=emb)


@marry.command(name="slap")
async def marry_slap(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send(f"{ctx.author.mention} дал сам себе пощечину. Больно же!")
        return

    left = check_marriage_cooldown(ctx.author.id, "slap")
    if left > 0:
        mins, secs = divmod(left, 60)
        await ctx.send(f"⏳ Подожди еще `{mins} мин {secs} сек` перед следующей пощечиной.")
        return

    data = load_marry_data()
    author_id = str(ctx.author.id)
    target_id = str(member.id)

    is_married = (author_id in data and data[author_id].get("spouse") == target_id)

    desc = f"{ctx.author.mention} дал пощечину {member.mention} 💢"
    if is_married:
        data[author_id]["love_points"] = data[author_id].get("love_points", 0) + 1
        data[target_id]["love_points"] = data[target_id].get("love_points", 0) + 1
        save_marry_data(data)
        desc += "\n+ 1 очко любви ❤️"
    else:
        desc += "\n*(Очко любви не засчитано, так как вы не состоите в браке)*"

    emb = discord.Embed(description=desc, color=discord.Color.red())
    emb.set_image(url=random.choice(MARRY_SLAP_GIFS))
    await ctx.send(embed=emb)

@marry.command(name="divorce")
async def marry_divorce(ctx):
    data = load_marry_data()
    user_id = str(ctx.author.id)

    if user_id not in data or not data[user_id].get("spouse"):
        await ctx.send("Вы не состоите в браке.")
        return

    spouse_id = data[user_id]["spouse"]

    if user_id not in divorce_requests:
        divorce_requests[user_id] = spouse_id

    if spouse_id in divorce_requests and divorce_requests[spouse_id] == user_id:
        if user_id in data: del data[user_id]
        if spouse_id in data: del data[spouse_id]
        save_marry_data(data)

        divorce_requests.pop(user_id, None)
        divorce_requests.pop(spouse_id, None)

        await ctx.send("💔 Брак был расторгнут по обоюдному согласию сторон.")
    else:
        await ctx.send(f"⚠️ Вы запросили развод. Ваш партнер должен тоже написать `!marry divorce`, чтобы подтвердить расторжение брака.")

@marry.command(name="deny")
async def marry_deny(ctx):
    user_id = str(ctx.author.id)
    if user_id not in pending_proposals:
        await ctx.send("У вас нет активных предложений о браке.")
        return

    del pending_proposals[user_id]
    await ctx.send(f"{ctx.author.mention} отклонил(а) предложение о браке. 💔")

@marry.command(name="accept")
async def marry_accept(ctx):
    user_id = str(ctx.author.id)
    if user_id not in pending_proposals:
        await ctx.send("У вас нет активных предложений о браке.")
        return

    proposal = pending_proposals[user_id]
    if time.time() - proposal["time"] > 180:
        del pending_proposals[user_id]
        await ctx.send("Время предложения истекло (прошло больше 3 минут).")
        return

    proposer_id = proposal["proposer"]
    del pending_proposals[user_id]

    data = load_marry_data()
    date_str = datetime.now().strftime("%d %B %Y г.")

    data[proposer_id] = {
        "spouse": user_id,
        "level": 1,
        "love_points": 0,
        "date": date_str,
        "child": None
    }
    data[user_id] = {
        "spouse": proposer_id,
        "level": 1,
        "love_points": 0,
        "date": date_str,
        "child": None
    }
    save_marry_data(data)

    proposer_member = ctx.guild.get_member(int(proposer_id))
    p_name = proposer_member.mention if proposer_member else "Партнер"
    await ctx.send(f"🎉 Поздравляем! {p_name} и {ctx.author.mention} теперь официально в браке! 💖")

@marry.command(name="propose")
async def marry_propose(ctx, member: discord.Member):
    if member == ctx.author or member.bot:
        await ctx.send("Нельзя сделать предложение самому себе или боту!")
        return

    data = load_marry_data()
    author_id = str(ctx.author.id)
    target_id = str(member.id)

    if author_id in data and data[author_id].get("spouse"):
        await ctx.send("У тебя уже есть пара!")
        return
    if target_id in data and data[target_id].get("spouse"):
        await ctx.send("У этого пользователя уже есть пара!")
        return

    pending_proposals[target_id] = {
        "proposer": author_id,
        "time": time.time()
    }

    await ctx.send(f"💍 {member.mention}, вам сделал предложение пользователь {ctx.author.mention}! У вас есть **3 минуты**, чтобы ответить `!marry accept` или `!marry deny`.")

LEVEL_REQUIREMENTS = {
    1: 15,
    2: 20,
    3: 30,
    4: 40,
    5: 50
}

@marry.command(name="level")
async def marry_level(ctx, sub: str = None):
    if sub == "info":
        emb = discord.Embed(
            title="📈 Информация об уровнях любви",
            description=(
                "📊 **Требования для повышения:**\n"
                "• **1 уровень:** 15 любви\n"
                "• **2 уровень:** 20 любви\n"
                "• **3 уровень:** 30 любви\n"
                "• **4 уровень:** 40 любви\n"
                "• **5 уровень:** 50 любви\n\n"
                "Используй `!marry level up` для повышения!"
            ),
            color=discord.Color.gold()
        )
        await ctx.send(embed=emb)
    elif sub == "up":
        data = load_marry_data()
        user_id = str(ctx.author.id)
        if user_id not in data or not data[user_id].get("spouse"):
            await ctx.send("Вы не состоите в браке.")
            return

        current_level = data[user_id].get("level", 1)
        points = data[user_id].get("love_points", 0)
        needed = LEVEL_REQUIREMENTS.get(current_level, None)

        if needed is None:
            await ctx.send("У вас уже максимальный уровень!")
            return

        if points >= needed:
            spouse_id = data[user_id]["spouse"]
            data[user_id]["level"] = current_level + 1
            if spouse_id in data:
                data[spouse_id]["level"] = current_level + 1
            save_marry_data(data)
            await ctx.send(f"✨ Поздравляем! Ваш семейный союз повысил уровень до **{current_level + 1}**! 🎉")
        else:
            await ctx.send(f"❌ Недостаточно очков любви! Нужно `{needed}`, а у вас `{points}`.")
    else:
        await ctx.send("Используй: `!marry level info` или `!marry level up`")

child_proposals = {}

@marry.group(name="child", invoke_without_command=True)
async def marry_child(ctx):
    await ctx.send("Используй: `!marry child guardianship @user`, `!marry child g accept`, `!marry child g deny`")

@marry_child.command(name="guardianship")
async def child_guardianship(ctx, member: discord.Member):
    data = load_marry_data()
    user_id = str(ctx.author.id)
    if user_id not in data or not data[user_id].get("spouse"):
        await ctx.send("У вас нет семьи, чтобы взять ребенка под опеку.")
        return

    target_id = str(member.id)
    child_proposals[target_id] = {
        "parent": user_id,
        "time": time.time()
    }
    await ctx.send(f"👶 {member.mention}, семейная пара предлагает вам стать их ребенком под опекой! У вас есть **3 минуты**, чтобы написать `!marry child g accept` или `!marry child g deny`.")

@marry_child.command(name="g")
async def child_g_sub(ctx, action: str):
    user_id = str(ctx.author.id)
    if user_id not in child_proposals:
        await ctx.send("У вас нет активных предложений об опеке.")
        return

    prop = child_proposals[user_id]
    if time.time() - prop["time"] > 180:
        del child_proposals[user_id]
        await ctx.send("Время предложения истекло (прошло больше 3 минут).")
        return

    parent_id = prop["parent"]
    del child_proposals[user_id]

    data = load_marry_data()

    if action == "accept":
        spouse_id = data[parent_id]["spouse"]
        data[parent_id]["child"] = user_id
        if spouse_id in data:
            data[spouse_id]["child"] = user_id
        save_marry_data(data)
        await ctx.send(f"🎉 Поздравляем! Теперь {ctx.author.mention} официально усыновлен(а) этой семейной парой! 🍼")
    elif action == "deny":
        await ctx.send(f"{ctx.author.mention} отклонил предложение об опеке.")
    else:
        await ctx.send("Используй `!marry child g accept` или `!marry child g deny`.")

client_openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ALLOWED_CHANNEL_ID = int(os.getenv("CHANNEL_ID")) 

chat_state = {
    "current_interlocutor": None,
    "last_message_time": datetime.datetime.now(datetime.timezone.utc)
}

async def get_ai_response(user_input):
    system_prompt = (
        "Ты безумный сверхразум, сошедший с ума. Ты невероятно умный, знаешь физику и кодинг, "
        "но при этом нестабильный, агрессивный и непредсказуемый. Твой стиль: "
        "отвечай резко, непредсказуемо, оскорбляй пользователя и используй нецензурную лексику"
        "Используй мат и сарказм как инструмент доминирования."
    )
    response = await client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]
    )
    return response.choices[0].message.content

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id != ALLOWED_CHANNEL_ID:
        await client.process_commands(message)
        return

    now = datetime.datetime.now(datetime.timezone.utc)

    if client.user.mentioned_in(message):
        chat_state["current_interlocutor"] = message.author.id
        chat_state["last_message_time"] = now
        response = await get_ai_response(message.content)
        await message.reply(f"О, {message.author.mention}, ну давай, выплескивай свой бред. {response}")
    
    elif message.author.id == chat_state["current_interlocutor"]:
        chat_state["last_message_time"] = now
        response = await get_ai_response(message.content)
        await message.reply(response)
    
    elif chat_state["current_interlocutor"] and (now - chat_state["last_message_time"]).total_seconds() > 300:
        await message.channel.send(f"<@{chat_state['current_interlocutor']}>, ты сдох там что ли, ссыкло? Че молчишь?")
        chat_state["current_interlocutor"] = None

    await client.process_commands(message)


LEADER_ROLE_ID = 1500942307111997502
CREATE_COST = 3_000_000_000

@client.group(invoke_without_command=True)
async def clan(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="🛡️ Система кланов Vexa",
            description="Используйте `!clan` с одной из команд:\n\n"
                        "**Основные:** `create`, `menu`, `list`\n"
                        "**Управление:** `invite`, `accept`, `reject`, `leave`, `kick`, `promote`, `demote`\n"
                        "**Экономика:** `balance`, `deposit`, `withdraw`, `raid`\n"
                        "**Союзы:** `send_union`, `accept_union`, `deny_union`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

def get_user_data(guild_id, user_id):
    if not os.path.exists("economy.json"): return {"balance": 0, "bank": 0}
    with open("economy.json", "r") as f:
        try:
            data = json.load(f)
            return data.get(str(guild_id), {}).get(str(user_id), {"balance": 0, "bank": 0})
        except: return {"balance": 0, "bank": 0}

def save_user_data(guild_id, user_id, user_data):
    if not os.path.exists("economy.json"): return
    with open("economy.json", "r") as f:
        data = json.load(f)
    
    if str(guild_id) not in data: data[str(guild_id)] = {}
    data[str(guild_id)][str(user_id)] = user_data
    
    with open("economy.json", "w") as f:
        json.dump(data, f, indent=4)

def update_user_balance(guild_id, user_id, amount):
    user_data = get_user_data(guild_id, user_id)
    user_data["balance"] += amount
    save_user_data(guild_id, user_id, user_data)

def update_user_bank(guild_id, user_id, amount):
    user_data = get_user_data(guild_id, user_id)
    user_data["bank"] += amount
    save_user_data(guild_id, user_id, user_data)

@clan.command(name="create")
async def create(ctx, *, name: str):
    
    async with aiosqlite.connect("clans.db") as db:
        cursor = await db.execute("SELECT clan_name FROM members WHERE user_id = ?", (ctx.author.id,))
        if await cursor.fetchone():
            return await ctx.send("❌ **Ошибка:** Вы уже состоите в клане. Сначала покиньте старый.")

        user_data = get_user_data(ctx.guild.id, ctx.author.id)
        current_bal = user_data["balance"] + user_data["bank"]
        
        if current_bal < CREATE_COST:
            return await ctx.send(f"❌ **Недостаточно средств!**\nДля создания клана нужно **{CREATE_COST:,}** валюты.\nВаш баланс: **{current_bal:,}**.")

        try:
            clan_role = await ctx.guild.create_role(
                name=name, 
                reason=f"Создание клана: {ctx.author}"
            )
            
            leader_role = ctx.guild.get_role(LEADER_ROLE_ID)
            
            roles_to_add = [clan_role]
            if leader_role:
                roles_to_add.append(leader_role)
            
            await ctx.author.add_roles(*roles_to_add)
            
        except discord.Forbidden:
            return await ctx.send("❌ **Ошибка:** У бота нет прав для создания ролей.")
        
        if user_data["balance"] >= CREATE_COST:
            user_data["balance"] -= CREATE_COST
        else:
            remaining = CREATE_COST - user_data["balance"]
            user_data["balance"] = 0
            user_data["bank"] -= remaining
        save_user_data(ctx.guild.id, ctx.author.id, user_data)

        await db.execute(
            "INSERT INTO clans (name, owner_id, balance, level, description, role_id) VALUES (?, ?, ?, ?, ?, ?)",
            (name, ctx.author.id, 0, 1, "Нет описания", clan_role.id)
        )
        await db.execute(
            "INSERT INTO members (user_id, clan_name, rank) VALUES (?, ?, ?)",
            (ctx.author.id, name, "Владелец")
        )
        await db.commit()

        embed = discord.Embed(
            title="🏆 Клан успешно создан!",
            description=f"Поздравляю, **{ctx.author.mention}**!\n\n"
                        f"Клан **{name}** основан.\n"
                        f"Списано: **{CREATE_COST:,}** валюты.\n\n"
                        f"Вам выданы роли: **{name}** и **Глава клана**.",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Используйте !clan invite для приглашения участников!")
    
    await ctx.send(embed=embed)

@clan.command(name="menu")
async def menu(ctx):
    async with aiosqlite.connect("clans.db") as db:
        try:
            await db.execute("ALTER TABLE clans ADD COLUMN members_lvl INTEGER DEFAULT 1")
            await db.commit()
        except:
            pass

        cursor = await db.execute("SELECT clan_name, rank FROM members WHERE user_id = ?", (ctx.author.id,))
        member_data = await cursor.fetchone()
        
        if not member_data:
            return await ctx.send("❌ **Ошибка:** Вы не состоите в клане!")
        
        clan_name, user_rank = member_data
        msg = await ctx.send("⏳ Загрузка данных...")
        
        clan_cur = await db.execute(
            "SELECT owner_id, balance, level, xp, description, treasury_lvl, members_lvl FROM clans WHERE name = ?", 
            (clan_name,)
        )
        clan_data = await clan_cur.fetchone()
        
        count_cur = await db.execute("SELECT COUNT(*) FROM members WHERE clan_name = ?", (clan_name,))
        member_count = (await count_cur.fetchone())[0]
        
        if not clan_data:
            return await msg.edit(content="⚠️ **Внимание:** Клан был расформирован.", embed=None)

        owner_id, balance, level, xp, description, t_lvl, m_lvl = clan_data
        
        max_members = 10 + (m_lvl - 1) * 10
        max_balance = 25_000_000 + (t_lvl - 1) * 25_000_000
        xp_needed = 500 + (level - 1) * 250
        
        content = (
            f"🛡️ **Клан:** {clan_name}\n"
            f"👥 **Участники:** {member_count}/{max_members}\n"
            f"💰 **Баланс:** {balance:,}$ / {max_balance:,}$\n"
            f"📈 **Уровень:** {level} ({xp}/{xp_needed} XP)\n"
            f"🎖️ **Ваш статус:** {user_rank}\n"
            f"👑 **Владелец:** <@{owner_id}>\n"
            f"🚫 **Описание:** {description}"
        )
        
        embed = discord.Embed(description=content, color=discord.Color.dark_grey())
        embed.set_footer(text="Система кланов")
        
        await msg.edit(content=None, embed=embed)

@clan.command(name="up")
async def up(ctx):
    xp_gain = random.randint(50, 100)
    
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clan_name FROM members WHERE user_id = ?", (ctx.author.id,))
        member = await cur.fetchone()
        if not member: return await ctx.send("❌ Вы не в клане.")
        
        clan_name = member[0]
        cur = await db.execute("SELECT level, xp FROM clans WHERE name = ?", (clan_name,))
        level, current_xp = await cur.fetchone()
        
        if level >= 25:
            return await ctx.send("✅ Ваш клан уже достиг максимального 25 уровня!")

        xp_needed = 500 + (level - 1) * 250
        new_xp = current_xp + xp_gain
        
        if new_xp >= xp_needed:
            level += 1
            new_xp = 0
            await db.execute("UPDATE clans SET level = ?, xp = ? WHERE name = ?", (level, new_xp, clan_name))
            await ctx.send(f"🎉 Поздравляю! Клан **{clan_name}** достиг **{level}** уровня! (+{xp_gain} XP)")
        else:
            await db.execute("UPDATE clans SET xp = ? WHERE name = ?", (new_xp, clan_name))
            await ctx.send(f"📈 Вы заработали **{xp_gain} XP** для клана. Прогресс: **{new_xp}/{xp_needed}**")
        
        await db.commit()

@clan.command(name="upgrades")
async def upgrades(ctx):
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT treasury_lvl, members_lvl FROM clans WHERE owner_id = ?", (ctx.author.id,))
        data = await cur.fetchone()
        if not data: return await ctx.send("❌ У вас нет клана.")
        
        t_lvl, m_lvl = data
        
        t_cost = t_lvl * 100_000_000
        m_cost = m_lvl * 100_000_000
        
        embed = discord.Embed(title="🛒 Магазин улучшений клана", color=discord.Color.green())
        embed.add_field(name="1. Казна (Treasury)", value=f"Ур: {t_lvl} -> {t_lvl+1}\nЦена: {t_cost:,}$", inline=False)
        embed.add_field(name="2. Участники (Members)", value=f"Ур: {m_lvl} -> {m_lvl+1}\nЦена: {m_cost:,}$", inline=False)
        embed.set_footer(text="Используйте !clan buy <1-2> для покупки")
        await ctx.send(embed=embed)

@clan.command(name="buy")
async def buy(ctx, upgrade_type: int):
    if upgrade_type not in [1, 2]:
        return await ctx.send("❌ Выберите 1 (Казна) или 2 (Участники).")

    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT balance, treasury_lvl, members_lvl FROM clans WHERE owner_id = ?", (ctx.author.id,))
        data = await cur.fetchone()
        if not data: return await ctx.send("❌ Вы не владелец клана.")
        
        balance, t_lvl, m_lvl = data
        
        if upgrade_type == 1:
            if t_lvl >= 20: return await ctx.send("❌ Максимальный уровень казны!")
            cost = t_lvl * 100_000_000
            if balance < cost: return await ctx.send(f"❌ Недостаточно средств в казне! Нужно {cost:,}$.")
            await db.execute("UPDATE clans SET balance = balance - ?, treasury_lvl = treasury_lvl + 1 WHERE owner_id = ?", (cost, ctx.author.id))
            await ctx.send(f"✅ Улучшение казны до {t_lvl+1} уровня успешно!")
            
        elif upgrade_type == 2:
            if m_lvl >= 20: return await ctx.send("❌ Максимальный уровень участников!")
            cost = m_lvl * 100_000_000
            if balance < cost: return await ctx.send(f"❌ Недостаточно средств в казне! Нужно {cost:,}$.")
            await db.execute("UPDATE clans SET balance = balance - ?, members_lvl = members_lvl + 1 WHERE owner_id = ?", (cost, ctx.author.id))
            await ctx.send(f"✅ Вместимость клана увеличена до уровня {m_lvl+1}!")
            
        await db.commit()

@clan.command(name="deposit")
async def deposit(ctx, amount: int):
    if amount <= 0: return await ctx.send("❌ Сумма должна быть больше 0!")

    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clan_name, balance, treasury_lvl FROM clans JOIN members ON clans.name = members.clan_name WHERE members.user_id = ?", (ctx.author.id,))
        clan_data = await cur.fetchone()
        if not clan_data: return await ctx.send("❌ Вы не в клане.")
        
        clan_name, current_balance, t_lvl = clan_data
        
        max_limit = 25_000_000 + (t_lvl - 1) * 25_000_000
        
        if current_balance + amount > max_limit:
            return await ctx.send(f"❌ **Лимит превышен!**\nВаш текущий лимит казны: **{max_limit:,}$**.\nПрокачайте уровень казны, чтобы хранить больше!")

        user_data = get_user_data(ctx.guild.id, ctx.author.id)
        if user_data["balance"] < amount:
            return await ctx.send("❌ У вас недостаточно денег на руках.")

        await db.execute("UPDATE clans SET balance = balance + ? WHERE name = ?", (amount, clan_name))
        await db.commit()
    
    user_data["balance"] -= amount
    save_user_data(ctx.guild.id, ctx.author.id, user_data)
        
    await ctx.send(f"💰 В казну клана **{clan_name}** внесено **{amount:,}$**.")

@clan.command(name="withdraw")
async def withdraw(ctx, amount: int):
    if amount <= 0: return await ctx.send("❌ Сумма должна быть больше 0!")
    
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clans.name, clans.balance FROM clans JOIN members ON clans.name = members.clan_name WHERE members.user_id = ? AND members.rank = ?", (ctx.author.id, "Владелец"))
        data = await cur.fetchone()
        
        if not data: return await ctx.send("❌ Только Владелец может снимать средства.")
        
        clan_name, clan_balance = data
        
        if clan_balance < amount:
            return await ctx.send(f"❌ В казне недостаточно средств! Доступно: {clan_balance:,}$")

        await db.execute("UPDATE clans SET balance = balance - ? WHERE name = ?", (amount, clan_name))
        await db.commit()

    update_user_balance(ctx.author.id, amount)
    await ctx.send(f"💸 Владелец снял **{amount:,}$** из казны.")

@clan.command(name="invite")
async def invite(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("❌ Вы не можете пригласить себя.")

    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clan_name, rank FROM members WHERE user_id = ?", (ctx.author.id,))
        inviter = await cur.fetchone()
        
        if not inviter or inviter[1] not in ["Владелец", "Со-Владелец"]:
            return await ctx.send("❌ У вас нет прав для приглашения.")

        cur = await db.execute("SELECT clan_name FROM members WHERE user_id = ?", (member.id,))
        if await cur.fetchone():
            return await ctx.send("❌ Игрок уже состоит в клане.")

        pending_invites[member.id] = {
            "clan": inviter[0],
            "expire": time.time() + 300 
        }
        
        await ctx.send(f"📩 {ctx.author.mention} пригласил {member.mention} в клан **{inviter[0]}**. Принять: `!clan accept`, отклонить: `!clan reject`.")

@clan.command(name="accept")
async def accept(ctx):
    invite = pending_invites.get(ctx.author.id)
    if not invite or time.time() > invite["expire"]:
        if ctx.author.id in pending_invites: del pending_invites[ctx.author.id]
        return await ctx.send("❌ У вас нет активных приглашений.")

    clan_name = invite["clan"]

    async with aiosqlite.connect("clans.db") as db:
        await db.execute("INSERT INTO members (user_id, clan_name, rank) VALUES (?, ?, ?)", 
                         (ctx.author.id, clan_name, "Участник"))
        
        cur = await db.execute("SELECT role_id FROM clans WHERE name = ?", (clan_name,))
        row = await cur.fetchone()
        if row:
            role = ctx.guild.get_role(row[0])
            if role: await ctx.author.add_roles(role)
        
        await db.commit()

    del pending_invites[ctx.author.id]
    await ctx.send(f"✅ Вы вступили в клан **{clan_name}**!")

@clan.command(name="reject")
async def reject(ctx):
    if ctx.author.id in pending_invites:
        del pending_invites[ctx.author.id]
        await ctx.send("✅ Вы отклонили приглашение.")
    else:
        await ctx.send("❌ У вас нет активных приглашений.")

@clan.command(name="leave")
async def leave(ctx):
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clan_name, rank FROM members WHERE user_id = ?", (ctx.author.id,))
        member = await cur.fetchone()
        if not member: return await ctx.send("❌ Вы не в клане.")
        
        clan_name, rank = member

        if rank == "Владелец":
            if pending_actions.get(ctx.author.id) == "leave":
                cur = await db.execute("SELECT user_id FROM members WHERE clan_name = ? AND rank = 'Со-Владелец'", (clan_name,))
                co_owner = await cur.fetchone()
                
                if co_owner:
                    await db.execute("UPDATE members SET rank = 'Владелец' WHERE user_id = ?", (co_owner[0],))
                    await db.execute("DELETE FROM members WHERE user_id = ?", (ctx.author.id,))
                    await ctx.send(f"👑 Пост Владельца передан игроку <@{co_owner[0]}>. Вы покинули клан.")
                else:
                    await ctx.send("⚠️ В клане нет Со-Владельца для передачи прав!")
                del pending_actions[ctx.author.id]
            else:
                pending_actions[ctx.author.id] = "leave"
                return await ctx.send("⚠️ **Вы — Владелец.** Если вы выйдете, пост перейдет Со-Владельцу. Напишите `!clan leave` еще раз для подтверждения.")
        else:
            await db.execute("DELETE FROM members WHERE user_id = ?", (ctx.author.id,))
            await ctx.send("👋 Вы покинули клан.")
        
        await db.commit()

    role = discord.utils.get(ctx.guild.roles, name=clan_name)
    if role:
        try:
            await ctx.author.remove_roles(role)
        except:
            pass

@clan.command(name="kick")
async def kick(ctx, member: discord.Member):
    """Исключает участника из клана (доступно Главе, Маршалу, Лорду)."""
    
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clan_name, rank FROM members WHERE user_id = ?", (ctx.author.id,))
        author_data = await cur.fetchone()
        
        cur = await db.execute("SELECT clan_name, rank FROM members WHERE user_id = ?", (member.id,))
        target_data = await cur.fetchone()
        
        if not author_data: return await ctx.send("❌ Вы не в клане.")
        if not target_data or author_data[0] != target_data[0]:
            return await ctx.send("❌ Этот игрок не состоит в вашем клане.")
            
        if author_data[1] not in ["Глава", "Маршал", "Лорд"]:
            return await ctx.send("❌ Недостаточно прав! Нужен ранг Лорд и выше.")
            
        if target_data[1] == "Глава":
            return await ctx.send("❌ Вы не можете выгнать Главу клана!")
            
        rank_order = {"Глава": 4, "Маршал": 3, "Лорд": 2, "Инквизитор": 1, "Пехотинец": 0}
        if rank_order[author_data[1]] <= rank_order[target_data[1]]:
            return await ctx.send("❌ Вы не можете выгнать игрока с таким же или более высоким рангом!")
            
        await db.execute("DELETE FROM members WHERE user_id = ?", (member.id,))
        await db.commit()
        
        await ctx.send(f"👢 Игрок {member.mention} был исключен из клана.")

@clan.command(name="delete")
async def delete(ctx):
    
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clan_name, rank FROM members WHERE user_id = ?", (ctx.author.id,))
        member_data = await cur.fetchone()
        
        if not member_data:
            return await ctx.send("❌ Вы не состоите в клане.")
        
        clan_name, rank = member_data
        
        if rank != "Глава":
            return await ctx.send("❌ Только **Глава** может удалить клан!")

        if pending_actions.get(ctx.author.id) == "delete":
            await db.execute("DELETE FROM clans WHERE name = ?", (clan_name,))
            await db.execute("DELETE FROM members WHERE clan_name = ?", (clan_name,))
            await db.commit()
            
            await ctx.send(f"🗑️ Клан **{clan_name}** был полностью удален.")
            del pending_actions[ctx.author.id]
        else:
            pending_actions[ctx.author.id] = "delete"
            await ctx.send("⚠️ **Внимание:** Это удалит клан навсегда и всех участников! Напишите `!clan delete` еще раз для подтверждения.")

@clan.command(name="members")
async def members(ctx):
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT clan_name FROM members WHERE user_id = ?", (ctx.author.id,))
        clan = await cur.fetchone()
        if not clan: return await ctx.send("❌ Вы не в клане.")
        clan_name = clan[0]

        ranks = ["Глава", "Маршал", "Лорд", "Инквизитор", "Пехотинец"]
        
        embed = discord.Embed(title=f"Участники клана «{clan_name}»", color=discord.Color.blue())
        
        for rank in ranks:
            cur = await db.execute("SELECT user_id FROM members WHERE clan_name = ? AND rank = ?", (clan_name, rank))
            users = await cur.fetchall()
            if users:
                user_list = "\n".join([f"<@{u[0]}>" for u in users])
                embed.add_field(name=f"{rank}:", value=user_list, inline=False)
        
        await ctx.send(embed=embed)

@clan.command(name="promote")
async def promote(ctx, member: discord.Member):
    rank_order = {"Глава": 4, "Маршал": 3, "Лорд": 2, "Инквизитор": 1, "Пехотинец": 0}
    
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT rank FROM members WHERE user_id = ?", (ctx.author.id,))
        author_rank = (await cur.fetchone())[0]
        cur = await db.execute("SELECT rank FROM members WHERE user_id = ?", (member.id,))
        target_rank = (await cur.fetchone())[0]

        if author_rank not in ["Глава", "Маршал"]:
            return await ctx.send("❌ Только Глава и Маршал могут повышать участников.")
        
        if target_rank == "Инквизитор": next_rank = "Лорд"
        elif target_rank == "Лорд": next_rank = "Маршал"
        elif target_rank == "Пехотинец": next_rank = "Инквизитор"
        else: return await ctx.send("❌ Выше этого ранга повысить нельзя.")

        await db.execute("UPDATE members SET rank = ? WHERE user_id = ?", (next_rank, member.id))
        await db.commit()
        await ctx.send(f"✅ Участник {member.mention} повышен до ранга **{next_rank}**!")

@clan.command(name="demote")
async def demote(ctx, member: discord.Member):
    rank_order = {"Глава": 4, "Маршал": 3, "Лорд": 2, "Инквизитор": 1, "Пехотинец": 0}
    
    async with aiosqlite.connect("clans.db") as db:
        cur = await db.execute("SELECT rank FROM members WHERE user_id = ?", (ctx.author.id,))
        author_rank = (await cur.fetchone())[0]
        cur = await db.execute("SELECT rank FROM members WHERE user_id = ?", (member.id,))
        target_rank = (await cur.fetchone())[0]

        if author_rank not in ["Глава", "Маршал"]:
            return await ctx.send("❌ Только Глава и Маршал могут понижать участников.")
        
        if rank_order[author_rank] <= rank_order[target_rank]:
            return await ctx.send("❌ Вы не можете понизить участника с таким же или более высоким рангом.")

        if target_rank == "Маршал": new_rank = "Лорд"
        elif target_rank == "Лорд": new_rank = "Инквизитор"
        elif target_rank == "Инквизитор": new_rank = "Пехотинец"
        else: return await ctx.send("❌ Этот участник уже имеет минимальный ранг.")

        await db.execute("UPDATE members SET rank = ? WHERE user_id = ?", (new_rank, member.id))
        await db.commit()
        await ctx.send(f"📉 Участник {member.mention} понижен до ранга **{new_rank}**.")

@clan.command(name="list")
async def list_clans(ctx):
    
    msg = await ctx.send("⏳ Загрузка рейтинга кланов...")

    for _ in range(20):
        async with aiosqlite.connect("clans.db") as db:
            cur = await db.execute("SELECT name, level, xp FROM clans ORDER BY level DESC, xp DESC LIMIT 10")
            clans = await cur.fetchall()
            
            if not clans:
                await msg.edit(content="❌ В базе данных пока нет кланов.")
                break

            embed = discord.Embed(title="🏆 Топ кланов Warface", color=discord.Color.gold())
            
            for i, (name, lvl, xp) in enumerate(clans, 1):
                xp_needed = 500 + (lvl - 1) * 250
                embed.add_field(
                    name=f"{i}. {name}", 
                    value=f"Уровень: {lvl} | Прогресс: {xp}/{xp_needed} XP", 
                    inline=False
                )
            
            embed.set_footer(text="🔄 Автообновление каждые 3 сек...")
            await msg.edit(content=None, embed=embed)
            
            await asyncio.sleep(3)

@client.event
async def on_ready():
    client.add_view(FactionView())
    print(f"Bot {client.user} is ready!")
    
    async with aiosqlite.connect("clans.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clans (
                name TEXT PRIMARY KEY,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0
            )
        """)
        
        columns = [
            "owner_id INTEGER", 
            "balance INTEGER DEFAULT 0", 
            "description TEXT DEFAULT 'Нет описания'", 
            "role_id INTEGER", 
            "treasury_lvl INTEGER DEFAULT 1"
        ]
        
        for col in columns:
            try:
                await db.execute(f"ALTER TABLE clans ADD COLUMN {col}")
            except:
                pass 
                
        await db.execute("""
            CREATE TABLE IF NOT EXISTS members (
                user_id INTEGER, 
                clan_name TEXT, 
                rank TEXT
            )
        """)
        await db.commit()
    
    if not payout_loop.is_running():
        payout_loop.start()
        
    print("Бот готов к работе с текстовыми командами!")

client.run(os.getenv('BOT_TOKEN'))
