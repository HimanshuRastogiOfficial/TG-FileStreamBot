# Taken from megadlbot_oss <https://github.com/eyaadh/megadlbot_oss/blob/master/mega/webserver/routes.py>
# Thanks to Eyaadh <https://github.com/eyaadh>

import re
import time
import math
import shutil
import psutil
import secrets
import logging
import asyncio
import mimetypes
from aiohttp import web
from WebStreamer.vars import Var
from aiohttp.http_exceptions import BadStatusLine
from WebStreamer.bot import multi_clients, work_loads
from WebStreamer.server.exceptions import FIleNotFound, InvalidHash
from WebStreamer import Var, utils, StartTime, __version__, StreamBot
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate


routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.HTTPFound(Var.REDIRECT_TO)

@routes.get("/status", allow_head=True)
async def root_route_handler(_):
    
    uptime = utils.get_readable_time(time.time() - StartTime)
    
    cpu = f"{psutil.cpu_percent(interval=0.5)}%"
    ram = f'{psutil.virtual_memory().percent}%'
        
    total, used, free = shutil.disk_usage('.')
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    disk = f"{psutil.disk_usage('/').percent}%"
    
    sent = humanbytes(psutil.net_io_counters().bytes_sent)
    recv = humanbytes(psutil.net_io_counters().bytes_recv)
        
    return web.json_response(
        {
            "status": "running",
            "uptime": uptime,
            "cpu_usage": cpu,
            "ram_usage": ram,
            "total_disk_space": total,
            "used_disk_space": used,
            "free_disk_space": free,
            "disk_percentage": disk,
            "data_sent": sent,
            "data_received": recv,
            "total_servers": len(multi_clients),
            "loads": dict(
                ("server" + str(c + 1), l)
                for c, (_, l) in enumerate(
                    sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
                )
            ),
            "version": __version__,
        }
    )

@routes.get(r"/{path}", allow_head=True)
async def stream_handler(request: web.Request):
    path = request.match_info["path"]
    if len(path) < 30:
        return web.HTTPFound(Var.REDIRECT_TO)
    elif len(path) > 34:
        return web.HTTPFound(Var.REDIRECT_TO)
    else:
        try:
            message = await StreamBot.send_cached_media(Var.BIN_CHANNEL, path)
        except ValueError:
            return web.json_response(
                {
                    "error": "The media you are trying to get is invalid.",
                    "solution": "Either mail us at error@hagadmansa.com or report it on Telegram at @HagadmansaChat.",
                    "tip": "Send us the URL too as a evidence, so that we can understand actual error."
                }
            )
        except ChannelPrivate:
            return web.json_response(
                {
                    "error": "Oh No! somehow the BIN_CHANNEL was deleted.",
                    "solution": "Either mail us at error@hagadmansa.com or report it on Telegram at @HagadmansaChat.",
                    "tip": "Send us the URL too as a evidence, so that we can understand actual error."
                }
            )
        except Exception as e:
            return web.json_response(
                {
                    "error": e, 
                    "solution": "Either mail us at error@hagadmansa.com or report it on Telegram at @HagadmansaChat.",
                    "tip": "Send us the URL too as a evidence, so that we can understand actual error."
                }
            ) 
        return await media_streamer(request, message.id)

class_cache = {}

async def media_streamer(request: web.Request, message_id: int):
    range_header = request.headers.get("Range", 0)
    
    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]
    
    if Var.MULTI_CLIENT:
        logging.info(f"Client {index} is now serving {request.remote}")

    if faster_client in class_cache:
        tg_connect = class_cache[faster_client]
        logging.debug(f"Using cached ByteStreamer object for client {index}")
    else:
        logging.debug(f"Creating new ByteStreamer object for client {index}")
        tg_connect = utils.ByteStreamer(faster_client)
        class_cache[faster_client] = tg_connect
    logging.debug("before calling get_file_properties")
    file_id = await tg_connect.get_file_properties(message_id)
    logging.debug("after calling get_file_properties")
    
    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = request.http_range.stop or file_size - 1

    req_length = until_bytes - from_bytes
    new_chunk_size = await utils.chunk_size(req_length)
    offset = await utils.offset_fix(from_bytes, new_chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = (until_bytes % new_chunk_size) + 1
    part_count = math.ceil(req_length / new_chunk_size)
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, new_chunk_size
    )

    mime_type = file_id.mime_type
    file_name = Var.CUSTOM_CAPTION + " " + file_id.file_name
    disposition = "attachment"
    if mime_type:
        if not file_name:
            try:
                file_name = f"{Var.CUSTOM_CAPTION} {secrets.token_hex(2)}.{mime_type.split('/')[1]}"
            except (IndexError, AttributeError):
                file_name = f"{Var.CUSTOM_CAPTION} {secrets.token_hex(2)}.unknown"
    else:
        if file_name:
            mime_type = mimetypes.guess_type(file_id.file_name)
        else:
            mime_type = "application/octet-stream"
            file_name = f"{Var.CUSTOM_CAPTION} {secrets.token_hex(2)}.unknown"
    return_resp = web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Range": f"bytes={from_bytes}-{until_bytes}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        },
    )

    if return_resp.status == 200:
        return_resp.headers.add("Content-Length", str(file_size))

    return return_resp
