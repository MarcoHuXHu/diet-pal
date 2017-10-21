#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from webframe import get, post
from model import User, Macro_Nutrition

#编写用于测试的URL处理函数
@get('/hello')
async def hello(*kw, request):
    # 如果这个函数有parameters，
    # 可以在signature中放入**kw，识别为VAR_KEYWORD（has_var_kw_args=True）如：hello(**kw, request)
    # 可以在signature中放入*，识别为KEYWORD_ONLY（has_named_kw_args=True）如：hello(*, request)
    print(kw) # {'user': 'marco'}
    user = 'World'
    # parameters在request.rel_url.query或者request.query中，
    # 参考webframe中：if request.method == 'GET':   qs = request.query_string
    if 'user' in request.rel_url.query:
        user = request.rel_url.query['user']
    body = '<h1>Hello {0}!</h1>'.format(user)
    return body

@get('/test')
async def test(request):
    foods = await Macro_Nutrition.find()
    return {
        '__template__': 'test.html',
        'foods': foods
    }

@get('/')
async def getAllFoods(request):
    foods = await Macro_Nutrition.find()
    return {
        '__template__': 'foods.html',
        'foods': foods
    }

# 对于返回json的api，只需要规定return的是dict，在webframe的response_middleware中就会把结果转化成json格式
@get('/api/foods')
async def api_getAllFoods(request):
    foods = await Macro_Nutrition.find()
    return dict(foods=foods)

@get('/api/users')
async def api_getAllUsers(request):
    users = await User.find()
    for user in users:
        user.password = '******'
    return dict(users=users)
