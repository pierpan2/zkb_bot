# bot.py
import discord
from discord.ext import commands
import io
import os
from logzhanfan import *
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.command()
async def zhanfan(ctx):
    if len(ctx.message.attachments) != 1:
        await ctx.send("Please attach a single .txt file.")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.filename.endswith('.txt'):
        await ctx.send("Please attach a .txt file.")
        return

    file_content = await attachment.read()
    lines = file_content.decode('utf-8').splitlines()

    img, fig = all_in_one(lines)

    # Convert Pillow image to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Convert Plotly figure to HTML and save to bytes
    fig_html = fig.to_html(full_html=False)
    html_byte_arr = io.BytesIO(fig_html.encode('utf-8'))
    html_byte_arr.seek(0)

    # Send the image
    img_file = discord.File(fp=img_byte_arr, filename='zhanfan.png')
    html_file = discord.File(fp=html_byte_arr, filename='figure.html')
    await ctx.reply(files=[img_file, html_file])

load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))
