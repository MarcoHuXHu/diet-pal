#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(level=logging.INFO)

import asyncio
from aiohttp import web

def index(request):
    return web.Response(body=b'<h1>Welcome!</h1>', content_type='text/html')

async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    server = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('Server start to listen http://127.0.0.1:9000')
    return  server

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

