# -*- coding: utf-8 -*-


import asyncio
import datetime
import pytest
import json

from fluent.sender import FluentSender
from unittest import mock


@pytest.mark.asyncio
async def test_elasticsearch_docker_index_template(DOCKER_IP, http_client):
    """ElasticSearch index templates are provisionned by the setup process."""

    url = 'http://%s:9200/_template' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()

    # Text logs (Docker containers' standard output & error streams).
    mappings = body['docker']['mappings']
    fields = mappings['_default_']['properties']
    assert '@timestamp' in fields
    fields = mappings['docker']['properties']
    assert 'container_name' in fields
    assert 'container_id' in fields
    assert 'source' in fields
    assert 'log' in fields


@pytest.mark.asyncio
async def test_elasticsearch_events_index_template(DOCKER_IP, http_client):
    """ElasticSearch index templates are provisionned by the setup process."""

    url = 'http://%s:9200/_template' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()

    # Structured logs.
    mappings = body['events']['mappings']
    fields = mappings['_default_']['properties']
    assert '@timestamp' in fields
    fields = mappings['events']['properties']
    assert fields['service']['type'] == 'string'
    assert fields['event']['type'] == 'string'


@pytest.mark.asyncio
async def test_elasticsearch_docker_index(DOCKER_IP, http_client):
    """ElasticSearch indexes are functionnal."""

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
async def test_elasticsearch_docker_index_auto_string(DOCKER_IP, http_client):
    """ElasticSearch indexes are functionnal."""

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
        # This field does not have an explicit type mapping.
        'dynamic_field': 123,
    })
    async with http_client.post(url, data=body) as resp:
        assert resp.status == 201
        body = await resp.text()

    # Wait until the record shows up in search results.
    await asyncio.sleep(datetime.timedelta(seconds=1).total_seconds())

    # Check the assigned type in the index (the template is not affected).
    url = 'http://%s:9200/docker-%04d-%02d-%02d' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    mappings = body['docker-%04d-%02d-%02d' % (
        today.year, today.month, today.day,
    )]['mappings']
    fields = mappings['_default_']['properties']
    assert '@timestamp' in fields
    fields = mappings['docker']['properties']
    assert fields['dynamic_field']['type'] == 'string'

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
        # TODO: figure out why this is a number!
        'dynamic_field': 123,
    }


@pytest.mark.asyncio
async def test_elasticsearch_events_index(DOCKER_IP, http_client):
    """ElasticSearch indexes are functionnal."""

    # Grab the current date (we'll need to use it several times and we don't
    # want to get flakey results when we execute the tests around midnight).
    today = datetime.date.today()

    # Clear the index.
    url = 'http://%s:9200/events-%s' % (
        DOCKER_IP,
        today.isoformat(),
    )
    async with http_client.delete(url) as resp:
        # May get 404 if we're the first test to run, but we'll get 200 if we
        # successfully delete the index.
        assert resp.status in (200, 404)

    # Post an event with `_type=events`.
    url = 'http://%s:9200/events-%s/events' % (
        DOCKER_IP,
        today.isoformat(),
    )
    body = json.dumps({
        'service': 'a-service',
        'event': 'an-event',
    })
    async with http_client.post(url, data=body) as resp:
        assert resp.status == 201
        body = await resp.text()

    # Wait until the record shows up in search results.
    await asyncio.sleep(datetime.timedelta(seconds=1).total_seconds())

    # Grab the record.
    url = 'http://%s:9200/events-%04d-%02d-%02d/events/_search' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['hits']['total'] == 1
    assert body['hits']['hits'][0]['_source'] == {
        'service': 'a-service',
        'event': 'an-event',
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
        'events-%04d-%02d-%02d' % (today.year, today.month, today.day)
    )
    assert int(index['docs.count']) == 1


@pytest.mark.asyncio
async def test_elasticsearch_events_index_auto_string(DOCKER_IP, http_client):
    """ElasticSearch indexes are functionnal."""

    # Grab the current date (we'll need to use it several times and we don't
    # want to get flakey results when we execute the tests around midnight).
    today = datetime.date.today()

    # Clear the index.
    url = 'http://%s:9200/events-%s' % (
        DOCKER_IP,
        today.isoformat(),
    )
    async with http_client.delete(url) as resp:
        # May get 404 if we're the first test to run, but we'll get 200 if we
        # successfully delete the index.
        assert resp.status in (200, 404)

    # Post an event with `_type=events`.
    url = 'http://%s:9200/events-%s/events' % (
        DOCKER_IP,
        today.isoformat(),
    )
    body = json.dumps({
        'service': 'a-service',
        'event': 'an-event',
        # This field does not have an explicit type mapping.
        'dynamic_field': 123,
    })
    async with http_client.post(url, data=body) as resp:
        assert resp.status == 201
        body = await resp.text()

    # Wait until the record shows up in search results.
    await asyncio.sleep(datetime.timedelta(seconds=1).total_seconds())

    # Check the assigned type in the index (the template is not affected).
    url = 'http://%s:9200/events-%04d-%02d-%02d' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    mappings = body['events-%04d-%02d-%02d' % (
        today.year, today.month, today.day,
    )]['mappings']
    fields = mappings['_default_']['properties']
    assert '@timestamp' in fields
    fields = mappings['events']['properties']
    assert fields['dynamic_field']['type'] == 'string'

    # Grab the record.
    url = 'http://%s:9200/events-%04d-%02d-%02d/events/_search' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['hits']['total'] == 1
    assert body['hits']['hits'][0]['_source'] == {
        'service': 'a-service',
        'event': 'an-event',
        # TODO: figure out why this is a number!
        'dynamic_field': 123,
    }


@pytest.mark.asyncio
async def test_kibana_docker_index_pattern(DOCKER_IP, http_client):
    """Kibana index patterns are provisionned by the setup procedure."""

    url = 'http://%s:9200/.kibana/index-pattern/docker-*' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['_type'] == 'index-pattern'
    assert body['_source']['title'] == 'docker-*'
    assert body['_source']['timeFieldName'] == '@timestamp'
    fields = json.loads(body['_source']['fields'])
    fields = {field['name']: field for field in fields}
    assert fields['@timestamp']['type'] == 'date'
    assert fields['@timestamp']['analyzed'] is False
    assert fields['container_name']['type'] == 'string'
    assert fields['container_name']['analyzed'] is False
    assert fields['container_id']['type'] == 'string'
    assert fields['container_id']['analyzed'] is False
    assert fields['log']['type'] == 'string'
    assert fields['log']['analyzed'] is False


@pytest.mark.asyncio
async def test_kibana_events_index_pattern(DOCKER_IP, http_client):
    """Kibana index patterns are provisionned by the setup procedure."""

    url = 'http://%s:9200/.kibana/index-pattern/events-*' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['_type'] == 'index-pattern'
    assert body['_source']['title'] == 'events-*'
    assert body['_source']['timeFieldName'] == '@timestamp'
    fields = json.loads(body['_source']['fields'])
    fields = {field['name']: field for field in fields}
    assert fields['@timestamp']['type'] == 'date'
    assert fields['@timestamp']['analyzed'] is False
    assert fields['service']['type'] == 'string'
    assert fields['service']['analyzed'] is False
    assert fields['event']['type'] == 'string'
    assert fields['event']['analyzed'] is False


@pytest.mark.asyncio
async def test_kibana_config(DOCKER_IP, http_client):
    """Kibana preferences are provisionned by the setup procedure."""

    url = 'http://%s:9200/.kibana/config/4.1.6' % (DOCKER_IP,)
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['_type'] == 'config'
    assert body['_source']['defaultIndex'] == 'events-*'


@pytest.mark.asyncio
async def test_fluentd_http_source_docker(DOCKER_IP, http_client):
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
async def test_fluentd_http_source_events(DOCKER_IP, http_client):
    """FluentD forwards HTTP records to ElasticSearch."""

    # Grab the current date (we'll need to use it several times and we don't
    # want to get flakey results when we execute the tests around midnight).
    today = datetime.date.today()

    # Clear the index.
    url = 'http://%s:9200/events-%s' % (
        DOCKER_IP,
        today.isoformat(),
    )
    async with http_client.delete(url) as resp:
        # May get 404 if we're the first test to run, but we'll get 200 if we
        # successfully delete the index.
        assert resp.status in (200, 404)

    # Post an event with a tag that matches `events.**` rule in `fluent.conf`.
    url = 'http://%s:8888/events.test.an-event' % (DOCKER_IP,)
    body = 'json=' + json.dumps({
        'some-field': 'some-value',
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
    url = 'http://%s:9200/events-%04d-%02d-%02d/events/_search' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['hits']['total'] == 1
    assert body['hits']['hits'][0]['_source'] == {
        'service': 'test',
        'event': 'an-event',
        'some-field': 'some-value',
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
        'events-%04d-%02d-%02d' % (today.year, today.month, today.day)
    )
    assert int(index['docs.count']) >= 1


@pytest.mark.asyncio
async def test_fluentd_forward_source_docker(DOCKER_IP, http_client):
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
    fluent = FluentSender('docker.test', host=DOCKER_IP, port=24224)
    fluent.emit('', {
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
async def test_fluentd_forward_source_events(DOCKER_IP, http_client):
    """FluentD forwards "native" records to ElasticSearch."""

    # Grab the current date (we'll need to use it several times and we don't
    # want to get flakey results when we execute the tests around midnight).
    today = datetime.date.today()

    # Clear the index.
    url = 'http://%s:9200/events-%s' % (
        DOCKER_IP,
        today.isoformat(),
    )
    async with http_client.delete(url) as resp:
        # May get 404 if we're the first test to run, but we'll get 200 if we
        # successfully delete the index.
        assert resp.status in (200, 404)

    # Post an event with a tag that matches `events.**` rule in `fluent.conf`.
    fluent = FluentSender('events.test', host=DOCKER_IP, port=24224)
    fluent.emit('an-event', {
        'some-field': 'some-value',
    })

    # Wait until the record shows up in search results.
    await asyncio.sleep(datetime.timedelta(seconds=3).total_seconds())

    # Grab the record.
    url = 'http://%s:9200/events-%04d-%02d-%02d/events/_search' % (
        DOCKER_IP, today.year, today.month, today.day,
    )
    async with http_client.get(url) as resp:
        assert resp.status == 200
        body = await resp.json()
    assert body['hits']['total'] == 1
    assert body['hits']['hits'][0]['_source'] == {
        'service': 'test',
        'event': 'an-event',
        'some-field': 'some-value',
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
        'events-%04d-%02d-%02d' % (today.year, today.month, today.day)
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
    async with http_client.put('http://%s:8082/file.json'
                               % DOCKER_IP, data=payload) as resp:
        assert resp.status in (201, 204)

    async with http_client.get('http://%s:8082/file.json'
                               % DOCKER_IP) as resp:
        assert resp.status == 200
        assert json.dumps(await resp.json()) == payload
        print(await resp.json())
