#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from webframe import get, post
from model import Macro_Nutrition

#编写用于测试的URL处理函数
@get('/test')
async def test(request):
    body='<h1>Hello World</h1>'
    return body

@get('/')
async def index(request):
    foods = await Macro_Nutrition.find()
    return {
        '__template__': 'index.html',
        'foods': foods
    }