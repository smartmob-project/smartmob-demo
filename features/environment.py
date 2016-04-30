# -*- coding: utf-8 -*-


import os
import re
import requests


def detect_docker_host():
    try:
        docker_host = os.environ['DOCKER_HOST']
    except KeyError:
        docker_host = '127.0.0.1'
    else:
        docker_host = re.match(r'^tcp://(.+):\d+$', docker_host).group(1)
    return docker_host


def before_all(context):
    context.docker_host = detect_docker_host()
    context.gitmesh = requests.get(
        'http://%s:8080/' % context.docker_host).json()
    context.smartmob_agent = requests.get(
        'http://%s:8081/' % context.docker_host).json()


def before_scenario(context, scenario):
    """Cleanup the Git server."""
    listing = requests.get(context.gitmesh['list']).json()
    for repo in listing['repositories']:
        r = requests.delete(repo['delete'])
        assert r.status_code == 200
    listing = requests.get(context.gitmesh['list']).json()
    assert listing['repositories'] == []
