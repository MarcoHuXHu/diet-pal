#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from model import User, Macro_Nutrition
from webframe import get, post


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

@post('api/register')
async def registerUser(username, password, email, nickname):
    pass





class APIError(Exception):
    ''' 基础的APIError，包含错误类型(必要)，数据(可选)，信息(可选) '''
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message


class APIValueError(APIError):
    ''' 表明输入数据有问题，data说明输入的错误字段 '''
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('Value: Invalid', field, message)


class APIResourceError(APIError):
    ''' 表明找不到资源，data说明资源名字 '''
    def __init__(self,field,message = ''):
        super(APIResourceError,self).__init__('Value: Not Found',field,message)


class APIPermissionError(APIError):
    ''' 接口没有权限 '''
    def __init__(self,message = ''):
        super(APIPermissionError,self).__init__('Permission: forbidden','Permission',message)