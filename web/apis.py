#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from model import User, Food, Record
from webframe import get, post, APIError, APIPermissionError, APIResourceError, APIValueError
from aiohttp import web
import re, hashlib, json, logging


# 对于返回json的api，只需要规定return的是dict，在webframe的response_middleware中就会把结果转化成json格式
@get('/api/foods')
async def getAllFoods():
    foods = await Food.find()
    return dict(foods=foods)

@get('/api/users')
async def getAllUsers():
    users = await User.find()
    for user in users:
        user.password = '******'
    return dict(users=users)

@post('/api/user')
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
    # 虽然传过来的password已经是加密过的了，这里统一在做一次摘要算法加密
    user = User(username=username, email=email,
                password=hashlib.sha1(password.encode('utf-8')).hexdigest(), phone=phone)
    await user.save()
    # make session cookie:
    return make_session(user)

@post('/api/authenticate')
async def authenticate(*, useremail, password):
    if not password:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.find(where='username=?', args=[useremail])
    if len(users) == 0:
        users = await User.find(where='email=?', args=[useremail])
    if len(users) == 0:
        raise APIValueError('User', 'Invalid User or password.')
    user = users[0]
    key = hashlib.sha1(password.encode('utf-8')).hexdigest()
    if key != user.password:
        raise APIValueError('User', 'Invalid User or password.')
    # authenticate OK, make session cookie:
    return make_session(user)

@get('/logout')
def logout(request):
    r = web.HTTPFound('/')
    r.set_cookie(configs.session.cookie_name, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

@post('/api/record')
async def addRecord(request, *, food_id, amount, record_time):
    checkadmin(request)
    food_id = food_id.strip()
    amount = float(amount)
    if not record_time:
        record_time = time.time()
    if not food_id:
        raise APIValueError('food', 'food must not be empty')
    if not amount or amount<0.00001:
        raise APIValueError('amount', 'amount must not be empty')
    record = Record(food_id=food_id, user_id=request.__user__.user_id, amount=amount, record_time=record_time)
    await record.save()
    return record

@get('/api/records')
async def get_records(request):
    checkadmin(request)
    records = await Record.find(where='user_id=?', args=[request.__user__.user_id])
    return dict(records=records)

def checkadmin(request):
    if not request.__user__:
        raise APIPermissionError()

from configs import configs
import time

def make_session(user):
    # make session cookie:
    r = web.Response()
    expire = configs.session.expire
    r.set_cookie(configs.session.cookie_name, user2cookie(user, time.time() + expire), max_age=expire, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

def user2cookie(user, expire):
    # 为了加强保密，这里的保存密码的key里面在加入一些其他信息
    key = '{0}{1}{2}{3}'.format(user.user_id, user.password, str(expire), configs.session.secret)
    L = [user.user_id, str(expire), hashlib.sha1(key.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        user_id, expire, key = L
        if float(expire) < time.time():
            return None
        user = await User.findByKey(user_id)
        if user is None:
            return None
        # 对从数据库中取出的user进行加密，然后与cookie中的信息对比
        key2 = '{0}{1}{2}{3}'.format(user.user_id, user.password, str(expire), configs.session.secret)
        if key != hashlib.sha1(key2.encode('utf-8')).hexdigest():
            logging.info('invalid user')
            return None
        user.password = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None