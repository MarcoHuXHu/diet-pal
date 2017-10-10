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
        try:
            cur = await connection.cursor(aiomysql.DictCursor)
            await cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            if not autocommit:
                await cur.commit()
        except BaseException:
            if not autocommit:
                await cur.rollback()
            raise
        return affected


def test():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_connection(loop, db='food_nutrition'))
    rs = loop.run_until_complete(select('select * from food;', ()))
    print(rs)

test()