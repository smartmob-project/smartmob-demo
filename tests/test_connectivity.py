# -*- coding: utf-8 -*-


import asyncio
import datetime
import pytest
import json

from pyfluent.client import FluentSender
from unittest import mock


@pytest.mark.asyncio
async def test_elasticsearch_index_templates(DOCKER_IP, http_client):
    """ElasticSearch index templates are provisionned by the setup process."""

    url = 'http://%s:9200/_template' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    mappings = body['docker']['mappings']
    fields = mappings['_default_']['properties']
    assert '@timestamp' in fields
    fields = mappings['docker']['properties']
    assert 'container_name' in fields
    assert 'container_id' in fields
    assert 'source' in fields
    assert 'log' in fields


@pytest.mark.asyncio
async def test_elasticsearch_index_data(DOCKER_IP, http_client):
    """ElasticSearch index templates is functionnal."""

    # Grab the current date (we'll need to use it several times and we don't
    # want to get flakey results when we execute the tests around midnight).
    today = datetime.date.today()

    # Clear the index.
    url = 'http://%s:9200/docker-%s' % (
        DOCKER_IP,
        today.isoformat(),
    )
    async with http_client.delete(url) as resp:
        # May get 404 if we're the first test to run, but we'll get 200 if we
        # successfully delete the index.
        assert resp.status in (200, 404)

    # Post an event with `_type=docker`.
    url = 'http://%s:9200/docker-%s/docker' % (
        DOCKER_IP,
        today.isoformat(),
    )
    body = json.dumps({
        'container_name': 'a-container-name',
        'container_id': 'a-container-id',
        'source': 'stdout',
        'log': 'Hello, world!',
    })
    async with http_client.post(url, data=body) as resp:
        assert resp.status == 201
        body = await resp.text()

    # Wait until the record shows up in search results.
    await asyncio.sleep(datetime.timedelta(seconds=1).total_seconds())

    # Grab the record.
    url = 'http://%s:9200/docker-%04d-%02d-%02d/docker/_search' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['hits']['total'] == 1
    assert body['hits']['hits'][0]['_source'] == {
        'container_name': 'a-container-name',
        'container_id': 'a-container-id',
        'source': 'stdout',
        'log': 'Hello, world!',
    }

    # Grab index stats, check that index exists and that we have our data.
    url = 'http://%s:9200/_cat/indices?v' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.text()
    print('STATS:')
    print(body)
    print('------')
    lines = body.split('\n')
    lines = [line.split() for line in lines if line.strip()]
    assert len(lines) >= 2
    stats = [dict(zip(lines[0], line)) for line in lines[1:]]
    stats = {index['index']: index for index in stats}
    index = stats.pop(
        'docker-%04d-%02d-%02d' % (today.year, today.month, today.day)
    )
    assert int(index['docs.count']) == 1


@pytest.mark.asyncio
async def test_kibana_index_patterns(DOCKER_IP, http_client):
    """Kibana index patterns are provisionned by the setup procedure."""

    url = 'http://%s:9200/.kibana/index-pattern/docker-*' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['_type'] == 'index-pattern'
    assert body['_source']['title'] == 'docker-*'
    assert body['_source']['timeFieldName'] == '@timestamp'


@pytest.mark.asyncio
async def test_kibana_config(DOCKER_IP, http_client):
    """Kibana preferences are provisionned by the setup procedure."""

    url = 'http://%s:9200/.kibana/config/4.1.6' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['_type'] == 'config'
    assert body['_source']['defaultIndex'] == 'docker-*'


@pytest.mark.asyncio
async def test_fluentd_http_source(DOCKER_IP, http_client):
    """FluentD forwards HTTP records to ElasticSearch."""

    # Grab the current date (we'll need to use it several times and we don't
    # want to get flakey results when we execute the tests around midnight).
    today = datetime.date.today()

    # Clear the index.
    url = 'http://%s:9200/docker-%s' % (
        DOCKER_IP,
        today.isoformat(),
    )
    async with http_client.delete(url) as resp:
        # May get 404 if we're the first test to run, but we'll get 200 if we
        # successfully delete the index.
        assert resp.status in (200, 404)

    # Post an event with a tag that matches `docker.**` rule in `fluent.conf`.
    url = 'http://%s:8888/docker.test' % (DOCKER_IP,)
    body = 'json=' + json.dumps({
        'container_name': 'a-container-name',
        'container_id': 'a-container-id',
        'source': 'stdout',
        'log': 'Hello, world!',
    })
    head = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    async with http_client.post(url, headers=head, data=body) as resp:
        assert resp.status == 200
        body = await resp.text()

    # Wait until the record shows up in search results.
    await asyncio.sleep(datetime.timedelta(seconds=3).total_seconds())

    # Grab the record.
    url = 'http://%s:9200/docker-%04d-%02d-%02d/docker/_search' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['hits']['total'] == 1
    assert body['hits']['hits'][0]['_source'] == {
        'container_name': 'a-container-name',
        'container_id': 'a-container-id',
        'source': 'stdout',
        'log': 'Hello, world!',
        '@timestamp': mock.ANY,
    }

    # Grab index stats, check that index exists and that we have our data.
    url = 'http://%s:9200/_cat/indices?v' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.text()
    print('STATS:')
    print(body)
    print('------')
    lines = body.split('\n')
    lines = [line.split() for line in lines if line.strip()]
    assert len(lines) >= 2
    stats = [dict(zip(lines[0], line)) for line in lines[1:]]
    stats = {index['index']: index for index in stats}
    index = stats.pop(
        'docker-%04d-%02d-%02d' % (today.year, today.month, today.day)
    )
    assert int(index['docs.count']) >= 1


@pytest.mark.asyncio
async def test_fluentd_forward_source(DOCKER_IP, http_client):
    """FluentD forwards "native" records to ElasticSearch."""

    # Grab the current date (we'll need to use it several times and we don't
    # want to get flakey results when we execute the tests around midnight).
    today = datetime.date.today()

    # Clear the index.
    url = 'http://%s:9200/docker-%s' % (
        DOCKER_IP,
        today.isoformat(),
    )
    async with http_client.delete(url) as resp:
        # May get 404 if we're the first test to run, but we'll get 200 if we
        # successfully delete the index.
        assert resp.status in (200, 404)

    # Post an event with a tag that matches `docker.**` rule in `fluent.conf`.
    fluent = FluentSender(DOCKER_IP, 24224, 'docker.test')
    fluent.send({
        'container_name': 'a-container-name',
        'container_id': 'a-container-id',
        'source': 'stdout',
        'log': 'Hello, world!',
    })

    # Wait until the record shows up in search results.
    await asyncio.sleep(datetime.timedelta(seconds=3).total_seconds())

    # Grab the record.
    url = 'http://%s:9200/docker-%04d-%02d-%02d/docker/_search' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['hits']['total'] == 1
    assert body['hits']['hits'][0]['_source'] == {
        'container_name': 'a-container-name',
        'container_id': 'a-container-id',
        'source': 'stdout',
        'log': 'Hello, world!',
        '@timestamp': mock.ANY,
    }

    # Grab index stats, check that index exists and that we have our data.
    url = 'http://%s:9200/_cat/indices?v' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.text()
    print('STATS:')
    print(body)
    print('------')
    lines = body.split('\n')
    lines = [line.split() for line in lines if line.strip()]
    assert len(lines) >= 2
    stats = [dict(zip(lines[0], line)) for line in lines[1:]]
    stats = {index['index']: index for index in stats}
    index = stats.pop(
        'docker-%04d-%02d-%02d' % (today.year, today.month, today.day)
    )
    assert int(index['docs.count']) >= 1


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
async def test_fileserver_flow(DOCKER_IP, http_client):
    payload = json.dumps({'MyData1': 'abcdef', 'MyData2': 'abcdef'})
    async with http_client.put('http://%s:8082/storage/file.json'
                               % DOCKER_IP, data=payload) as resp:
        assert resp.status in (201, 204)

    async with http_client.get('http://%s:8082/storage/file.json'
                               % DOCKER_IP) as resp:
        assert resp.status == 200
        assert json.dumps(await resp.json()) == payload
        print(await resp.json())
