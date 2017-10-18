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
    async with __pool.acquire() as connection:
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
        # fields用来保存非primaryKey的列名，primaryKey用来保存primaryKey的列名，储存primaryKey主要是为了Delete的时候方便
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
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

        # SQL中列名由``包围，比如`user_id`
        sql_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = name # 假设表名和类名一致
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        attrs['__select__'] = 'select `%s`, %s from `%s`' % \
                              (primaryKey, ', '.join(sql_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % \
                              (tableName, ', '.join(sql_fields), primaryKey, ('%s?') % ('?, '*len(sql_fields)))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % \
                              (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).column_name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            logging.info('Cannot find {0}'.format(key))
            return None

    def __setattr__(self, key, value):
        self[key] = value

    # find和findByKey都是返回Model类型的方法，所以要用classmethod，而其他CRD操作只是返回操作结果，所以非classmethod
    @classmethod
    async def find(cls, where=None, args=None, **kw):
        #find objects by where clause.
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    async def findByKey(cls, pk):
        ' find object by primary key. '
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.__getattr__, self.__fields__))
        args.append(self.__getattr__(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.error('failed to insert record: affected rows: %s' % rows)

    async def change(self):
        args = list(map(self.__getattr__, self.__fields__))
        args.append(self.__getattr__(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.error('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.__getattr__(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.error('failed to remove by primary key: affected rows: %s' % rows)

