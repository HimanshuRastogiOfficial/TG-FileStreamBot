# This file is a part of TG-FileStreamBot
# Coding : Jyothis Jayanth [@EverythingSuckz]

import logging
from pyrogram import filters
from WebStreamer.vars import Var
from WebStreamer.bot import StreamBot
from WebStreamer.utils.file_properties import getNew, fileId, fileSize

@StreamBot.on_message(filters.command('gen'))
async def getStreamlink(bot, message):
    
    if message.from_user.id not in [1250003833, 5099088450]:
        return
    
    replied = message.reply_to_message
    
    if not replied:
        return await message.reply("Reply to a message.")
    
    if replied.photo:
        return await message.reply(
            text="Don't send me photos, send them as document.",
            quote=True
        )
    
    if not replied.caption:
        return await message.reply("Give me a file name as a Quote.")
        
    try:
        await message.reply(
            text=f"{Var.URL}{getNew(fileId(replied))[0]}/{replied.caption.replace(' ', '%20')}",
            quote=True
        )
    except Exception as e:
        await message.reply(
            text=e,
            quote=True
        )
