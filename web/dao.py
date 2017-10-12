#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, aiomysql, logging

async def create_connection(loop, **kwargs):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        loop=loop,
        host=kwargs.get('host', 'localhost'),
        port=kwargs.get('port', 3306),
        user=kwargs.get('user', 'root'),
        password=kwargs.get('password','password'),
        db=kwargs.get('db'),
        charset=kwargs.get('charset', 'utf8'),
        autocommit=kwargs.get('autocommit', True),
        maxsize=kwargs.get('maxsize', 10),
        minsize=kwargs.get('minsize', 1)
    )

async def select(sql, args, size=None):
    logging.info('SQL: %s' % sql)
    global __pool
    async with __pool.acquire() as connection:
        # connection.cursor(aiomysql.DictCursor)使得结果以Dict的形式返回
        cur = await connection.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        return rs

# 这里对于autocommit暂时没有仔细研究，等到数据库需要处理事务的时候在看看
async def execute(sql, args, autocommit=True):
    logging.info('SQL: %s' % sql)
    global __pool
    async with __pool.acquire as connection:
        if not autocommit:
            await connection.begin()
        cur = await connection.cursor(aiomysql.DictCursor)
        try:
            await cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            if not autocommit:
                await cur.commit()
        except BaseException:
            if not autocommit:
                await cur.rollback()
            raise
        return affected


# 各种数据库中数据类型的基类
class Field(object):
    def __init__(self, column_name, column_type, primary_key):
        self.column_name = column_name
        self.column_type = column_type
        self.primary_key = primary_key

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_name, self.column_type)

# 各种数据库中数据类型相关的类
class StringField(Field):
    def __init__(self, column_name=None, column_type ='VARCHAR(50)', primary_key=False):
        super().__init__(column_name, column_type, primary_key)

class IntegerField(Field):
    def __init__(self, column_name=None, column_type ='INT', primary_key=False):
        super().__init__(column_name, column_type, primary_key)

class FloatField(Field):
    def __init__(self, column_name=None, column_type ='FLOAT', primary_key=False):
        super().__init__(column_name, column_type, primary_key)

class TextField(Field):
    def __init__(self, column_name=None, column_type ='TEXT', primary_key=False):
        super().__init__(column_name, column_type, primary_key)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        # 如果Model层的类没有给定__table__，则以类名为默认值
        tableName = attrs.get('__table__', None) or name
        mappings = dict()
        # fields用来保存非primaryKey的列名，primaryKey用来保存primaryKey的列名，这俩好像没啥用
        fields = []; primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                print('Found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise BaseException('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise BaseException('Primary key not found.')

        for k in mappings.keys():
            attrs.pop(k)

        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = name # 假设表名和类名一致
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
        tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            logging.error('KeyError: object has no attribute {0}'.format(key))
            return None

    def __setattr__(self, key, value):
        self[key] = value







def test():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_connection(loop, db='awesome'))
    rs = loop.run_until_complete(select('select * from user;', ()))
    print(rs)

test()