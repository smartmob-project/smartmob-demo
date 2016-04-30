# -*- coding: utf-8 -*-


import aiohttp
import os
import pytest
import re


@pytest.fixture
def DOCKER_IP():
    try:
        endpoint = os.environ['DOCKER_HOST']
    except KeyError:
        endpoint = '127.0.0.1'
    else:
        endpoint = re.match(r'^tcp://(.+?):\d+$', endpoint).group(1)
    return endpoint


@pytest.yield_fixture
def http_client(event_loop):
    with aiohttp.ClientSession() as session:
        yield session
