#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 考虑到app.py中利用的是aiohttp，在绑定url和对应方法，以及返回response方面比较复杂
# 这里对aiohttp进行封装，DIY一个web framework来

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

def request_method_decorator(path, method):
    '''
    Define decorator ('/path', 'get/post')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__route__ = path
        wrapper.__method__ = method
        return wrapper
    return decorator

get = functools.partial(request_method_decorator,method = 'GET')
post = functools.partial(request_method_decorator,method = 'POST')


# 用RequestHandler()来封装一个URL处理函数
# RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL对应函数。
# 然后把结果转换为web.Response对象，这样，就气到了封装aiohttp框架的要求

class RequestHandler(object):

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_args = self.has_request_args(fn)
        self._has_var_kw_args = self.has_var_kw_args(fn)
        self._has_named_kw_args = self.has_named_kw_args(fn)
        self._named_kw_args = self.get_named_kw_args(fn)
        self._required_kw_args = self.get_required_kw_args(fn)

    # RequestHandler是一个类，由于定义了__call__()方法，因此可以将其实例视为函数。
    async def __call__(self, request):
        kw = None
        if self._has_var_kw_args or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest(text='Missing Content_Type.')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest(text='JSON body must be object.')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest(text='Unsupported Content-Type: %s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_args and self._named_kw_args:
                # remove all unamed kw:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            # check named arg:
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_args:
            kw['request'] = request
        # check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest(text='Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))
        # 调用对应对URL函数_func()，即fn，返回response
        try:
            r = await self._func(**kw)
            return r
        except BaseException as e:
            return e #dict(error=e.error, data=e.data, message=e.message)

    # 运用inspect模块，创建几个函数用以获取URL处理函数与request参数之间的关系
    def get_required_kw_args(self, fn):
        args = []
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
                args.append(name)
        return tuple(args)

    def get_named_kw_args(self, fn):
        args = []
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                args.append(name)
        return tuple(args)

    def has_named_kw_args(self, fn):
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                return True

    def has_var_kw_args(self, fn):
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                return True

    # 判断是否含有名叫'request'参数，且该参数是否为最后一个参数
    def has_request_args(self, fn):
        params = inspect.signature(fn).parameters
        sig = inspect.signature(fn)
        found = False
        for name,param in params.items():
            if name == 'request':
                found = True
                continue # 跳出当前循环，进入下一个循环
            if found and (str(param.kind) != 'VAR_POSITIONAL' and str(param.kind) != 'KEYWORD_ONLY' and str(param.kind != 'VAR_KEYWORD')):
                raise ValueError('request parameter must be the last named parameter in function: %s%s'%(fn.__name__,str(sig)))
        return found


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))

# add_route函数，用来注册一个URL处理函数
# 主要起验证函数是否有包含URL的响应方法与路径信息，以及将函数变为协程。
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))

# 直接导入文件，批量注册一个URL处理函数
def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)


