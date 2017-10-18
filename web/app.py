#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from webframe import add_route, add_routes, add_static
from webframe import response_factory
import dao

import os
import asyncio
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

import logging
logging.basicConfig(level=logging.INFO)


async def init(loop):
    path = os.getcwd()
    app = web.Application(loop=loop, middlewares=[response_factory])
    await dao.create_connection(loop, db='diet_pal')
    # 初始化Jinja2，这里值得注意是设置文件路径的path参数
    init_jinja2(app, path=path+r'/templates')#,filters=dict(datetime=datetime_filter))
    add_routes(app, 'web.controller')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('Server started at http://127.0.0.1:9000...')
    return srv

# 初始化jinja2，以便其他函数使用jinja2模板
def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()

