#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from webframe import get, post
import apis

#编写用于测试的URL处理函数
@get('/hello')
def hello(request, **kw):
    # 如果这个函数有parameters，
    # 可以在signature中放入**kw，识别为VAR_KEYWORD（has_var_kw_args=True）如：hello(**kw, request)
    print(kw) # {'user': 'marco'}
    user = 'World'
    # parameters在request.rel_url.query或者request.query中，
    # 参考webframe中：if request.method == 'GET':   qs = request.query_string
    if 'user' in request.rel_url.query:
        user = request.rel_url.query['user']
    body = '<h1>Hello {0}!</h1>'.format(user)
    return body

@get('/')
async def index(request):
    # foods = await Macro_Nutrition.find()
    # 调用api来得到数据，由于api要从数据库取数据，为了不阻塞服务器处理其他请求，这里需要异步
    foods = (await apis.getAllFoods())['foods']
    return {
        '__template__': 'foods.html',
        'foods': foods,
        '__user__':request.__user__
    }

@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

@get('/login')
def login():
    return {
        '__template__': 'login.html'
    }
