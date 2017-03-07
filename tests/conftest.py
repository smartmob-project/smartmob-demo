# -*- coding: utf-8 -*-


import aiohttp
import pytest


@pytest.fixture(scope='session')
def elasticsearch(docker_ip, docker_services):
    url = 'http://%s:%d' % (
        docker_ip,
        docker_services.port_for('elasticsearch', 9200)
    )
    return url


@pytest.fixture(scope='function')
def http_client(event_loop):
    with aiohttp.ClientSession() as session:
        yield session
