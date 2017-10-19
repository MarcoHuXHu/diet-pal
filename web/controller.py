#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from webframe import get, post
from model import Macro_Nutrition

#编写用于测试的URL处理函数
@get('/hello')
async def hello(request):
    user = 'World'
    if 'user' in request.query:
        user = request.query['user']
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
async def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    foods = await Macro_Nutrition.find()
    return {
        '__template__': 'foods.html',
        'foods': foods
    }