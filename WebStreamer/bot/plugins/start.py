from pyrogram import filters
from WebStreamer.bot import StreamBot

@StreamBot.on_message(filters.command(["start"]))
async def start(bot, message):
    
    if message.from_user.id not in [1250003833, 5099088450]:
        return
    else:
        await message.reply("Hey, I'm Alive.")
