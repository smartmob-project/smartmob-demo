# -*- coding: utf-8 -*-


import pytest
import json


@pytest.mark.asyncio
async def test_gitmesh(DOCKER_IP, http_client):
    async with http_client.get('http://%s:8080/' % DOCKER_IP) as resp:
        assert resp.status == 200
        print(await(resp.json()))


@pytest.mark.asyncio
async def test_smartmob_agent(DOCKER_IP, http_client):
    async with http_client.get('http://%s:8081/' % DOCKER_IP) as resp:
        assert resp.status == 200
        print(await(resp.json()))


@pytest.mark.asyncio
async def test_fileserver_get_file(DOCKER_IP, http_client):
    async with http_client.get('http://%s:8082/storage/' % DOCKER_IP) as resp:
        assert resp.status == 200


@pytest.mark.asyncio
async def test_fileserver_put_file(DOCKER_IP, http_client):
    payload = json.dumps({'MyData1': 'abcdef', 'MyData2': 'abcdef'})
    async with http_client.put('http://%s:8082/storage/file.json'
                               % DOCKER_IP, data=payload) as resp:
        assert resp.status in (201, 204)
