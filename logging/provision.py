# -*- coding: utf-8 -*-


import errno
import os
import os.path
import re
import socket
import time
import timeit

try:
    from urllib.error import URLError
    from urllib.request import urlopen, Request
    from urllib.parse import urljoin
    def autoclose(x):
        return x
except ImportError:
    # Python 2.7.
    from contextlib import contextmanager
    from urllib2 import URLError, urlopen, Request
    from urlparse import urljoin
    @contextmanager
    def autoclose(x):
        try:
            yield x
        finally:
            x.close()


here = os.path.dirname(os.path.abspath(__file__))


def readfile(path):
    """Read a binary file's contents into a byte string."""
    with open(path, 'rb') as stream:
        return stream.read()


def resolve_elasticsearch_url(elasticsearch_port=9200):
    """Deduce ElasticSearch URL from ``DOCKER_HOST``."""
    docker_host = os.environ.get('DOCKER_HOST', '')
    if docker_host:
        match = re.match(r'^tcp://(.+?):\d+$', docker_host)
        docker_ip = match.group(1)
    else:
        docker_ip = '127.0.0.1'
    return 'http://%s:%d' % (docker_ip, elasticsearch_port)


def check_status(req, rep, status_codes={200, 201}):
    """Check HTTP status against a set of expected status codes."""
    if not isinstance(status_codes, (list, set)):
        status_codes = [status_codes]
    status_code = rep.getcode()
    if status_code not in status_codes:
        # TODO: log information about the request and the response to help
        #       diagnostics...
        raise Exception(
            'HTTP %d was unexpected (expecting one of %r).' % (
                status_code,
                status_codes,
            )
        )


def provision(elasticsearch_url, clock=timeit.default_timer, timeout=30.0):
    """Upload logging configurations to ElasticSearch."""

    # Wait until ElasticSearch is responsive.
    #
    # NOTE: this is just a convenience to tolerate for the ElasticSearch Docker
    #       container to start up.  After the timeout is elapsed, proceed as
    #       usual to get "real" diagnostics as if we didn't poll at all.
    ref = clock()
    while (clock() - ref) < timeout:
        try:
            req = Request(url=elasticsearch_url)
            with autoclose(urlopen(req)) as rep:
                check_status(req, rep, {200})
                break
        except (ConnectionResetError, URLError) as error:
            # Even though URLError is a subclass of OSError and has an
            # ``errno`` attribute, it seems like it's set to ``None``, so we
            # cannot portably test for ``errno.ECONNREFUSED``...
            time.sleep(1.0)

    # Upload ElasticSearch index templates (1 of 2).
    req = Request(
        url=urljoin(elasticsearch_url, '_template/docker'),
        data=readfile(
            os.path.join(here, 'elasticsearch-index-template-docker.json')
        ),
    )
    with autoclose(urlopen(req)) as rep:
        check_status(req, rep, {200, 201})

    # Upload ElasticSearch index templates (2 of 2).
    req = Request(
        url=urljoin(elasticsearch_url, '_template/events'),
        data=readfile(
            os.path.join(here, 'elasticsearch-index-template-events.json')
        ),
    )
    with autoclose(urlopen(req)) as rep:
        check_status(req, rep, {200, 201})

    # Upload Kibana index patterns (1 of 2).
    req = Request(
        url=urljoin(elasticsearch_url, '.kibana/index-pattern/docker-*'),
        data=readfile(
            os.path.join(here, 'kibana-index-pattern-docker.json')
        ),
    )
    with autoclose(urlopen(req)) as rep:
        check_status(req, rep, {200, 201})

    # Upload Kibana index patterns (2 of 2).
    req = Request(
        url=urljoin(elasticsearch_url, '.kibana/index-pattern/events-*'),
        data=readfile(
            os.path.join(here, 'kibana-index-pattern-events.json')
        ),
    )
    with autoclose(urlopen(req)) as rep:
        check_status(req, rep, {200, 201})

    # Upload Kibana configuration (default index pattern, etc.).
    req = Request(
        url=urljoin(elasticsearch_url, '.kibana/config/4.1.6'),
        data=readfile(
            os.path.join(here, 'kibana-configuration.json')
        ),
    )
    with autoclose(urlopen(req)) as rep:
        check_status(req, rep, {200, 201})


if __name__ == '__main__':
    provision(resolve_elasticsearch_url())
