# -*- coding: utf-8 -*-


import os
import os.path
import re
import requests
import testfixtures


def detect_docker_host():
    try:
        docker_host = os.environ['DOCKER_HOST']
    except KeyError:
        docker_host = '127.0.0.1'
    else:
        docker_host = re.match(r'^tcp://(.+):\d+$', docker_host).group(1)
    return docker_host


def cleanup_gitmesh(context):
    # Cleanup repositories.
    listing = requests.get(context.gitmesh['list']).json()
    for repo in listing['repositories']:
        r = requests.delete(repo['delete'])
        assert r.status_code == 200
    listing = requests.get(context.gitmesh['list']).json()
    assert listing['repositories'] == []


def cleanup_smartmob(context):
    listing = requests.get(context.smartmob_agent['list']).json()
    for process in listing['processes']:
        r = requests.post(process['delete'])
        assert r.status_code == 200
    listing = requests.get(context.smartmob_agent['list']).json()
    assert listing['processes'] == []


def before_all(context):
    context.docker_host = detect_docker_host()
    context.gitmesh = requests.get(
        'http://%s:8080/' % context.docker_host).json()
    context.smartmob_agent = requests.get(
        'http://%s:8081/' % context.docker_host).json()

    # Make sure we get off to a fresh start.
    cleanup_gitmesh(context)
    cleanup_smartmob(context)


def before_scenario(context, scenario):
    """Ensure tests run with a clean environment."""

    # Make sure tests can resolve test data.
    context.test_root = os.path.dirname(os.path.abspath(__file__))

    # Move into a new working folder for each scenario.
    context.old_cwd = os.getcwd()
    context.tempdir = testfixtures.TempDirectory(create=True)
    os.chdir(context.tempdir.path)


def after_scenario(context, scenario):
    """Restore the environment after each test."""

    # Cleanup test leftovers.
    cleanup_gitmesh(context)
    cleanup_smartmob(context)

    # Restore the old working directory and delete any temporary files.
    os.chdir(context.old_cwd)
    del context.old_cwd
    context.tempdir.cleanup()
