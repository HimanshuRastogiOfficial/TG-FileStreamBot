import os
import time
import shutil
import traceback
from pytz import timezone 
from pyrogram import filters
from datetime import datetime
#from pyrogram import FloodWait
from WebStreamer.bot import StreamBot
from WebStreamer.utils.progress import progress

def listToString(s):
  str1 = " "
  return (str1.join(s))
  
@StreamBot.on_message(filters.command("rx"))
async def rename(bot, message):
  
  try:
  
    if message.from_user.id not in [1250003833, 5099088450]:
        return
  
    rn = await message.reply(text="`Processing...`", reply_to_message_id=message.reply_to_message.id)
    replied = message.reply_to_message
    
    if (" " in message.text) and (replied is not None):
     
        file_name = message.text.split('|')[0][18::]
        caption = message.text.split('|')[1]
        t = datetime.now(timezone("Asia/Kolkata")).strftime('%H:%M:%S')
        location = f"downloads/{t}/{file_name}"
        
        time_ = time.time()
        await bot.download_media(
            message=replied,
            file_name=location,
            progress=progress,
            progress_args=(f'**Name:** `{file_name}`\n**Status:** Downloading...', rn, time_)
        )
            
        time_ = time.time()
        await message.reply_document(
            document=location,
            thumb='WebStreamer/resources/hagadmansa.png',
            caption=caption,
            progress=progress,
            reply_to_message_id=message.reply_to_message.id,
            progress_args=(f'**Name:** `{file_name}`\n**Status:** Uploading...', rn, time_)
        )
        shutil.rmtree(f"downloads/{t}")
        await rn.delete()
    else:
        await rn.edit('Reply to file and provide a new name.')
  #except FloodWait as f:
      #await asyncio.sleep(f.x)
  except Exception as e:
      txt = traceback.format_exc() 
      shutil.rmtree(f"downloads/{t}")
      await message.reply(f"**Traceback Info:**\n`{txt}`\n**Error Text:**\n`{e}`")
      return await rn.delete()
