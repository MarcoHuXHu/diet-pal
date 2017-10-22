#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
import json

# 函数返回值转化为web.response对象（必要的一个middleware）
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