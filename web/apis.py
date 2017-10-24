#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from model import User, Macro_Nutrition
from webframe import get, post, APIError, APIPermissionError, APIResourceError, APIValueError
from aiohttp import web
import re, hashlib, json


# 对于返回json的api，只需要规定return的是dict，在webframe的response_middleware中就会把结果转化成json格式
@get('/api/foods')
async def getAllFoods():
    foods = await Macro_Nutrition.find()
    return dict(foods=foods)

@get('/api/users')
async def getAllUsers():
    users = await User.find()
    for user in users:
        user.password = '******'
    return dict(users=users)

@post('/api/registerUser')
async def registerUser(*, username, password, email, phone):
    _RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
    _RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')
    username = username.strip()
    password = password.strip()
    email = email.strip()
    phone = phone.strip()
    if not username:
        raise APIError('username')
    if not password or not _RE_SHA1.match(password):
        raise APIError('password')
    if not email or not _RE_EMAIL.match(email):
        raise APIError('email')
    users = await User.find('username=? or email=?', [username, email])
    if len(users) > 0:
        raise APIError('register:failed', '', 'Email or Username is already in use.')
    sp = hashlib.sha1()
    sp.update(password.encode('utf-8'))
    user = User(username=username, email=email, password=sp.hexdigest(), phone=phone)
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r
