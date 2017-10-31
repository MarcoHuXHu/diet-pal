#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
import json
from configs import configs

# 函数返回值转化为web.response对象（必要的一个middleware）
# 当服务器接收到请求，先调用此中间件，其中调用RequestHandler并执行相应controller，然后中间件对结果封装成response
async def response_factory(app, handler):
    async def response_middleware(request):
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r,str):
            if r.startswith('redirect:'): # 重定向
                return web.HTTPFound(r[9:]) # 转入别的网站
            resp =  web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charsest=utf-8'
            return resp
        if isinstance(r,dict):
            template = r.get('__template__')
            if template is None: # 序列化JSON，传递数据
                # https://docs.python.org/2/library/json.html#basic-usage
                resp = web.Response(body=json.dumps(
                    r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                return resp
            else: #jinja2模板
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default，错误
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response_middleware


# 对于每个URL处理函数，如果我们都去写解析cookie的代码，那会导致代码重复很多次。
# 利用middle在处理URL之前，把cookie解析出来，并将登录用户绑定到request对象上，这样，后续的URL处理函数就可以直接拿到登录用户：
# 这里采用middleware新写法

from apis import cookie2user

@web.middleware
async def authenticate(request, handler):
    # init and get cookie
    # 事实上每一次请求都会从cookie中拿uid，然后去数据库里面找一次user，然后赋值给request.__user__
    # 所以即使是用api登录
    request.__user__ = None
    cookie_str = request.cookies.get(configs.session.cookie_name)
    if cookie_str:
        user = await cookie2user(cookie_str)
        if user:
            request.__user__ = user
    return (await handler(request))

# async def authenticate(app,handler):
#     async def auth(request):
#         request.__user__ = None #初始化
#         cookie_str = request.cookies.get(configs.session.cookie_name)
#         if cookie_str:
#             user = await cookie2user(cookie_str)
#             if user:
#                 request.__user__ = user
#         return await handler(request)
#     return auth