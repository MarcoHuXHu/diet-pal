#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from aiohttp import web
from webframe import add_route, add_routes, add_static
from webframe import response_factory
import logging
logging.basicConfig(level=logging.INFO)

import asyncio

#编写web框架测试
async def init(loop):
    app = web.Application(loop=loop, middlewares=[response_factory])#, logger_factory])
    #init_jinja2(app,filters=dict(datetime=datetime_filter),path = r"E:\learningpython\web_app\templates")#初始化Jinja2，这里值得注意是设置文件路径的path参数
    add_routes(app,'web.controller')
    add_static(app)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('Server started at http://127.0.0.1:9000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

