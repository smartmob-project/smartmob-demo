# -*- coding: utf-8 -*-


import json
import pytest


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
