import asyncio
import os
import random
from datetime import datetime, timezone, timedelta
import json
import logging
import discord
from discord.ext import commands
from discord import app_commands

logging.basicConfig(filename='backup_log.txt', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
intents = discord.Intents.all()
intents.message_content = True
intents.members = True  # Нужно для получения списка участников
intents.reactions = True  # Нужно для отслеживания реакций
warnings = {}

# Инициализация бота
bot = commands.Bot(command_prefix="$", intents=intents)

# ID ролей и пользователей
AUTHORIZED_ROLE_ID = 2346463643  # Замените на ID роли, которая может выполнять команду
OWNER_ID = 21324  # Замените на ваш ID пользователя Discord
USER_IDS_TO_DELETE = []  # Замените на ID пользователей, сообщения которых нужно удалятьa
TARGET_MESSAGE_ID = 0  # Замените на ID сообщения, за которым нужно следить

# Лог-файл для реакций
LOG_FILE = "reaction_log.txt"

# Функция для отправки GIF сообщения
async def send_gif(channel, gif_url):
    await channel.send(gif_url)

async def send_picture(channel):
    picture_folder = 'aska'
    pictures = os.listdir(picture_folder)
    picture_file = random.choice(pictures)
    picture_path = os.path.join(picture_folder, picture_file)
    await channel.send(file=discord.File(picture_path))

async def send_random_message(channel):
    messages = ["ваши сообщения"
    ]

    message = random.choice(messages)
    await channel.send(message)

async def check_time():
    while True:
        # Получить текущее время в UTC+3
        current_time = datetime.now(timezone.utc) + timedelta(hours=3)
        print(f"Проверка времени: {current_time.isoformat()}")  # Строка для отладки

        # Проверка на 7:30
        if current_time.hour == 7 and current_time.minute == 0:
            channel = bot.get_channel(1285274560102404199)
            if channel:
                await send_gif(channel,
                               'https://tenor.com/view/asuka-langley-langley-asuka-evangelion-neon-genesis-evangelion-gif-8796834862117941782')
            else:
                print("Канал не найден для сообщения в 7:30")

        # Проверка на время с 8:00 до 21:00
        elif 8 <= current_time.hour < 22:
            channel = bot.get_channel(1285274560102404199)  # 1237117168567582831

            # Проверка на время отправки случайного сообщения (каждые 2 часа)
            if current_time.hour % 2 == 0 and current_time.minute == 0:
                if channel:
                    await send_random_message(channel)
                else:
                    print("Канал не найден для случайного сообщения")

        # Проверка на 22:00
        elif current_time.hour == 0 and current_time.minute == 0:
            channel = bot.get_channel(1285274562090766445)
            if channel:
                await send_picture(channel)
            else:
                print("Канал не найден для сообщения в 22:00")

        # Проверка на 23:00
        elif current_time.hour == 23 and current_time.minute == 0:
            channel = bot.get_channel(1285274560102404199)
            if channel:
                await send_gif(channel, 'https://tenor.com/view/asuka-langley-gif-26114337')
            else:
                print("Канал не найден для сообщения в 23:00")

        # Пауза на 1 минуту перед следующей проверкой времени
        await asyncio.sleep(60)

@bot.event
async def on_ready():
    print('Я родилась!')
    await bot.change_presence(activity=discord.Game(name="Сосмарк"))
    await bot.tree.sync()  # Синхронизация команд с сервером
    bot.loop.create_task(check_time())

@bot.event
async def on_message(message):
    # Пересылка личных сообщений владельцу бота
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        owner = bot.get_user(OWNER_ID)
        if owner:
            embed = discord.Embed(title="Новое личное сообщение", color=discord.Color.blue())
            embed.add_field(name="Отправитель", value=message.author.name, inline=True)
            embed.add_field(name="Содержание", value=message.content, inline=False)
            embed.set_thumbnail(url=message.author.avatar.url)
            embed.timestamp = datetime.now()
            await owner.send(embed=embed)
        else:
            print("Владелец не найден для пересылки сообщения")

    # Проверка, если пользователь в списке на удаление сообщения
    if message.author.id in USER_IDS_TO_DELETE:
        try:
            await message.delete()
            print(f"Сообщение пользователя {message.author.name} удалено.")
        except discord.Forbidden:
            print(f"Не удалось удалить сообщение пользователя {message.author.name} (Запрещено).")
        except discord.HTTPException as e:
            print(f"Ошибка при удалении сообщения пользователя {message.author.name}: {e}")

    await bot.process_commands(message)

# Реакция на добавление реакции
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.message_id == TARGET_MESSAGE_ID:
        user = bot.get_user(payload.user_id)
        emoji = payload.emoji

        log_entry = f"{user} добавил реакцию {emoji} на сообщение ID {TARGET_MESSAGE_ID}\n"
        with open(LOG_FILE, "a") as log:
            log.write(log_entry)
        print(log_entry)  # Вывод лога в консоль для оперативного мониторинга

# Реакция на удаление реакции
@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.message_id == TARGET_MESSAGE_ID:
        user = bot.get_user(payload.user_id)
        emoji = payload.emoji

        log_entry = f"{user} удалил реакцию {emoji} с сообщения ID {TARGET_MESSAGE_ID}\n"
        with open(LOG_FILE, "a") as log:
            log.write(log_entry)
        print(log_entry)  # Вывод лога в консоль для оперативного мониторинга

# Проверка наличия у пользователя авторизованной роли
def has_authorized_role(interaction: discord.Interaction):
    # Проверяем, если пользователь — владелец, возвращаем True
    if interaction.user.id == OWNER_ID:
        return True
    # Иначе проверяем наличие роли с AUTHORIZED_ROLE_ID
    return any(role.id == AUTHORIZED_ROLE_ID for role in interaction.user.roles)

# Определение слэш-команды с проверкой роли
@bot.tree.command(name="skhnotify", description="Уведомить пользователей в указанных ролях с сообщением")
@app_commands.describe(roles="Роли для уведомления (через запятую, можно упоминания)", message="Сообщение для отправки")
@app_commands.check(has_authorized_role)
async def skhnotify(interaction: discord.Interaction, roles: str, message: str):
    roles_list = [role.strip() for role in roles.split(",")]
    found_roles = []

    for role_str in roles_list:
        # Проверка на упоминание роли
        if role_str.startswith("<@&") and role_str.endswith(">"):
            role_id = int(role_str[3:-1])
            role = discord.utils.get(interaction.guild.roles, id=role_id)
        else:
            role = discord.utils.get(interaction.guild.roles, name=role_str)

        if role:
            found_roles.append(role)
        else:
            await interaction.response.send_message(f"Роль '{role_str}' не найдена.", ephemeral=True)
            print(f"Роль '{role_str}' не найдена")
            return

    await interaction.response.send_message("Уведомление отправлено.", ephemeral=True)

    for role in found_roles:
        for member in role.members:
            try:
                await member.send(message)
                print(f"Сообщение отправлено {member.name} {message}")
            except discord.Forbidden:
                await interaction.followup.send(f"Не смогла отправить сообщение {member.name} (Запрещено)", ephemeral=True)
                print(f"Не смогла отправить сообщение {member.name} (Запрещено)")
            except discord.HTTPException as e:
                await interaction.followup.send(f"Ошибка при отправке сообщения {member.name}: {e}", ephemeral=True)
                print(f"Ошибка при отправке сообщения {member.name}: {e}")
            await asyncio.sleep(1)  # Добавление задержки для избежания ограничения по скорости

@skhnotify.error
async def skhnotify_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)

@bot.tree.command(name="ban", description="Забанить пользователя на сервере.")
@app_commands.describe(user="Пользователь для бана", reason="Причина бана")
@app_commands.check(has_authorized_role)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Причина не указана"):
    try:
        # Отправляем причину бана пользователю
        try:
            await user.send(f"Вы были забанены на сервере. Причина: {reason}")
        except discord.Forbidden:
            print(f"Не удалось отправить сообщение пользователю {user.name} (Запрещено).")
        except discord.HTTPException as e:
            print(f"Ошибка при отправке сообщения пользователю {user.name}: {e}")

        # Выполняем бан пользователя
        await user.ban(reason=reason)
        await interaction.response.send_message(f"Пользователь {user.mention} был забанен. Причина: {reason}")
    except discord.Forbidden:
        await interaction.response.send_message(f"У меня нет прав банить {user.mention}.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Не удалось забанить {user.mention}. Ошибка: {e}", ephemeral=True)

# Новая слэш-команда для отправки сообщения в определённый канал
@bot.tree.command(name="send_message", description="Отправить сообщение в указанный канал")
@app_commands.describe(channel="Канал для отправки сообщения", message="Сообщение для отправки")
@app_commands.check(has_authorized_role)
async def send_message(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    try:
        await channel.send(message)
        await interaction.response.send_message(f"Сообщение отправлено в канал {channel.name}.", ephemeral=True)
        print(f"Сообщение отправлено в канал {channel.name}")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Ошибка при отправке сообщения в канал {channel.name}: {e}", ephemeral=True)
        print(f"Ошибка при отправке сообщения в канал {channel.name}: {e}")


# Новая слэш-команда для пересылки сообщения пользователю
@bot.tree.command(name="reply", description="Переслать сообщение указанному пользователю")
@app_commands.describe(user="Пользователь для получения сообщения", message="Сообщение для отправки")
async def forward_message(interaction: discord.Interaction, user: discord.User, message: str):
    try:
        await user.send(message)
        await interaction.response.send_message(f"Сообщение отправлено пользователю {user.name}.", ephemeral=True)
        print(f"Сообщение отправлено {user.name}")
    except discord.Forbidden:
        await interaction.response.send_message(f"Не удалось отправить сообщение пользователю {user.name} (Запрещено).", ephemeral=True)
        print(f"Не смогла отправить сообщение {user.name} (Запрещено)")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"Ошибка при отправке сообщения пользователю {user.name}: {e}", ephemeral=True)
        print(f"Ошибка при отправке сообщения пользователю {user.name}: {e}")

@forward_message.error
async def forward_message_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)


@bot.tree.command(name="backup", description="Создать резервную копию данных сервера.")
@app_commands.check(has_authorized_role)
async def backup(interaction: discord.Interaction):
    guild = interaction.guild

    guild_data = {
        "guild_name": guild.name,
        "guild_id": guild.id,
        "roles": [
            {
                "name": role.name,
                "id": role.id,
                "permissions": role.permissions.value,
                "position": role.position
            } for role in guild.roles
        ],
        "channels": [
            {
                "name": channel.name,
                "id": channel.id,
                "type": str(channel.type),
                "category": channel.category.name if channel.category else None,
                "position": channel.position
            } for channel in guild.channels
        ],
        "members": [
            {
                "name": member.name,
                "id": member.id,
                "roles": [role.name for role in member.roles]
            } for member in guild.members
        ]
    }

    backup_filename = f"{guild.name}_backup.json"

    # Ensure the directory exists
    if not os.path.exists("backups"):
        os.makedirs("backups")

    backup_filepath = os.path.join("backups", backup_filename)

    with open(backup_filepath, "w", encoding='utf-8') as backup_file:
        json.dump(guild_data, backup_file, ensure_ascii=False, indent=4)

    logging.info(f"Backup created for guild: {guild.name} (ID: {guild.id})")

    await interaction.response.send_message("Резервная копия данных сервера успешно создана.", ephemeral=True)

    logging.info("Backup process completed successfully.")


@backup.error
async def backup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("У вас нет разрешения для выполнения этой команды.", ephemeral=True)
        logging.warning(f"Unauthorized backup attempt by {interaction.user.name} (ID: {interaction.user.id})")
    else:
        await interaction.response.send_message("Произошла ошибка при создании резервной копии.", ephemeral=True)
        logging.error(f"Error during backup: {error}")

@bot.tree.command(name="mcskin", description="Показать скин игрока Minecraft по его нику.")
async def mcskin(interaction: discord.Interaction, nickname: str):
    # Формируем URL для получения скина игрока по нику
    skin_url = f"https://minotar.net/avatar/{nickname}.png"

    # Создаем embed-сообщение для отображения скина
    embed = discord.Embed(title=f"Скин игрока {nickname}", color=discord.Color.green())
    embed.set_image(url=skin_url)
    embed.set_footer(text=f"Скин игрока {nickname} предоставлен Minotar")

    # Отправляем сообщение в канал
    await interaction.response.send_message(embed=embed)


# Команда для выдачи предупреждения
@bot.tree.command(name="warn", description="Выдать предупреждение пользователю.")
@app_commands.describe(user="Пользователь для предупреждения", reason="Причина предупреждения")
@app_commands.check(has_authorized_role)
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if user.id not in warnings:
        warnings[user.id] = []

    warnings[user.id].append(reason)
    await user.send(f"Вы получили предупреждение на сервере. Причина: {reason}")
    await interaction.response.send_message(f"Пользователю {user.mention} выдано предупреждение. Причина: {reason}",
                                            ephemeral=True)

    if len(warnings[user.id]) >= 3:  # Например, после 3 предупреждений можно забанить пользователя
        await user.ban(reason="Получено 3 предупреждения.")
        await interaction.followup.send(f"Пользователь {user.mention} был забанен за 3 предупреждения.", ephemeral=True)

@bot.tree.command(name="spam_user", description="Spam a user with a specified message.")
@app_commands.describe(user="The user to spam", message="The message to spam", count="Number of times to send the message")
@app_commands.check(has_authorized_role)
async def spam_user(interaction: discord.Interaction, user: discord.User, message: str, count: int):
    if count <= 0:
        await interaction.response.send_message("The count must be greater than 0.", ephemeral=True)
        return

    for _ in range(count):
        try:
            await user.send(message)
            print(f"Spam message sent to {user.name}")
            await asyncio.sleep(1)  # To avoid rate limiting
        except discord.Forbidden:
            await interaction.response.send_message(f"Cannot send message to {user.name} (Forbidden).", ephemeral=True)
            print(f"Cannot send message to {user.name} (Forbidden).")
            break
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Error sending message to {user.name}: {e}", ephemeral=True)
            print(f"Error sending message to {user.name}: {e}")
            break

    await interaction.response.send_message(f"Spammed {user.name} with {count} messages.", ephemeral=True)


async def main():
    async with bot:
        await bot.start("token")

# Start the bot and web server
asyncio.run(main())

