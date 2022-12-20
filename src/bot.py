import discord
from discord import app_commands
from src import responses
from src import log

logger = log.setup_logger(__name__)

config = responses.get_config()

isPrivate = False


class aclient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/chat | /help")

import re
async def send_message(message, user_message):
    try:
        ab=None
        if isinstance(message,discord.Interaction):
            await message.response.defer(ephemeral=isPrivate)
            sss = await responses.handle_response(user_message)
            response = f'>{user_message}\n'+re.sub(r"\A[\n\s]*",'',sss,re.MULTILINE)
            ab=message.followup
        elif isinstance(message,discord.Message):
            sss = await responses.handle_response(user_message)
            response = re.sub(r"\A[\n\s]*", '', sss, re.MULTILINE)
            ab=message.channel
        else:
            raise Exception(f"Странное сообщение, {message}")
        if len(response)>1900:
            if "```" in response:
                parts = response.split("```")
                await ab.send(parts[0])
                code_block = parts[1].split("\n")
                formatted_code_block = ""
                for line in code_block:
                    while len(line)>50:
                        formatted_code_block += line[:50]+"\n"
                        line = line[50:]
                    formatted_code_block += line+"\n"
                await ab.send("```"+formatted_code_block+"```")
                await ab.send(parts[2])
            else:
                response_chunks = [response[i:i+1900]
                                   for i in range(0, len(response), 1900)]
                for chunk in response_chunks:
                    await ab.send(chunk)
        else:
            if isinstance(ab,discord.TextChannel):
                await ab.send(response,reference=message)
            else:
                await ab.send(response)
    except Exception as e:
        if ab:
            await ab.send(f"> **Error: Something [{e}] went wrong, please try again later!**")

async def send_start_prompt(client):
    import os
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r") as f:
                prompt = f.read()
                logger.info(f"Send starting prompt with size {len(prompt)}")
                responseMessage = await responses.handle_response(prompt)
                if(config['discord_channel_id']):
                    channel = client.get_channel(int(config['discord_channel_id']))
                    await channel.send(responseMessage)
            logger.info(f"Starting prompt response: {responseMessage}")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


def run_discord_bot():
    client = aclient()

    @client.event
    async def on_message(message: discord.Message):
        if message.author == client.user: #Свои сообщения пропускает
            return
        #if message.guild.id!=715722540206653462: #Ограничение по айди сервера
        #    return
        for x in message.mentions: #Если в сообщение есть упоминания
            if x.id==client.user.id: #И одно из них - это упоминание бота
                logger.info(f"\x1b[31m{str(message.author)}\x1b[0m : '{message.content}' ({str(message.channel)})") #Это лог
                ss=message.content.replace(client.user.mention,'') #Вырезаю из строки упоминание
                await send_message(message,ss) #Отправка ответа
                return
        if message.reference: #Если сообщение - ответ на что-то
            msg=await message.channel.fetch_message(message.reference.message_id) #Загружаются по умолчанию последние 100 сообщений в
            # каналах, и те, которые во время работы бота присылали, если оно старое, то его содержание и прочее недоступны, и нужно их принудительно
            if msg.author==client.user: #Если ответ на упоминание этого бота
                logger.info(f"\x1b[31m{str(message.author)}\x1b[0m : '{message.content}' ({str(message.channel)})") #Это лог
                await send_message(message, message.content)
                return
    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        user_message = message
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
        await send_message(interaction, user_message)

    @client.tree.command(name="private", description="Toggle private access")
    async def private(interaction: discord.Interaction):
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if not isPrivate:
            isPrivate = not isPrivate
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send("> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**")
        else:
            logger.info("You already on private mode!")
            await interaction.followup.send("> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**")

    @client.tree.command(name="public", description="Toggle public access")
    async def public(interaction: discord.Interaction):
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if isPrivate:
            isPrivate = not isPrivate
            await interaction.followup.send("> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**")
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send("> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**")
            logger.info("You already on public mode!")



    @client.tree.command(name="help", description="Show help for the bot")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(":star:**BASIC COMMANDS** \n    `/chat [message]` Chat with ChatGPT!\n    `/public` ChatGPT switch to public mode \n    For complete documentation, please visit https://github.com/Zero6992/chatGPT-discord-bot")
        logger.info(
            "\x1b[31mSomeone need help!\x1b[0m")

    TOKEN = config['discord_bot_token']
    client.run(TOKEN)
