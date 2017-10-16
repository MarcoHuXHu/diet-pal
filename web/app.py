#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
logging.basicConfig(level=logging.INFO)

import asyncio


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

