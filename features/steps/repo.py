# -*- coding: utf-8 -*-


import json
import requests

from behave import given, when, then


@given('I create a new "{name}" repository')
def create_repository(context, name):
    r = requests.post(context.gitmesh['create'], data=json.dumps({
        'name': name,
    }))
    assert r.status_code == 201


@when('I list existing repositories')
def list_repositories(context):
    listing = requests.get(context.gitmesh['list']).json()
    context.repository_listing = listing['repositories']
    print(context.repository_listing)


@then('I should see "{name}" in the repository listing')
def repository_exists(context, name):
    print(context.repository_listing)
    assert name in {repo['name'] for repo in context.repository_listing}
