#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 考虑到app.py中利用的是aiohttp，在绑定url和对应方法，以及返回response方面比较复杂
# 这里对aiohttp进行封装，DIY一个web framework来

import asyncio, os, inspect, logging, functools, json
from urllib import parse
from aiohttp import web

# 这个装饰器的目的是给URL函数加入两个属性，一个是path，即对应的URL，另一个是method，即get/post等
# 这里的*是为了留给其他参数的，比如request等等
def request_method_decorator(path, method):
    '''
    Define decorator ('/path', 'get/post')
    '''
    def decorator(func):
        # 使用functools模块的wraps装饰器，更正函数名
        # 不然函数名，即__name__为wrapper，则之后调用inspect模块检查函数的参数就会有问题
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__route__ = path
        wrapper.__method__ = method
        return wrapper
    return decorator

get = functools.partial(request_method_decorator,method = 'GET')
post = functools.partial(request_method_decorator,method = 'POST')


# 被add_route和add_routes调用，其中app是aiohttp中web模块的web.Application，
# fn是指各个URL函数，放在controller中
# 用RequestHandler()来封装一个URL处理函数
# RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL对应函数。
# 然后把结果转换为web.Response对象，这样，就起到了封装aiohttp框架的要求
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
        sig = inspect.signature(fn)
        params = sig.parameters
        found = False
        for name, param in params.items():
            if name == 'request':
                found = True
                continue
            if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
                raise ValueError(
                    'request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
        return found


# add_route函数，用来注册一个URL处理函数
# 主要起验证函数是否有包含URL的响应方法与路径信息，以及将函数变为协程。
# 最终还是要通过aiohttp中web模块的router完成
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

# 添加静态文件夹的路径，类似于SimpleHTTPServer
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


# middleware
# 这里引入aiohttp框架的web.Application()中的middleware参数。
    # middleware（拦截器），一个URL在被某个函数处理前，可以经过一系列的middleware的处理。
    # 一个middleware可以改变URL的输入、输出，甚至可以决定不继续处理而直接返回。
# 当创建web.appliction的时候，可以设置middleware参数，
# 而创建middleware类似于装饰器，通过一些middleware factory(协程函数)。
# 这些middleware factory接受一个app实例，一个handler两个参数，并返回一个新的handler。

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
            if template is None: # 序列化JSON那章，传递数据
                # https://docs.python.org/2/library/json.html#basic-usage
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
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