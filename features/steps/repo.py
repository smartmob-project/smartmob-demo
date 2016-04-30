# -*- coding: utf-8 -*-


import json
import requests

from behave import given, when, then


@given('There are no repositories')
def empty_listing(context):
    listing = requests.get(context.gitmesh['list']).json()
    assert listing['repositories'] == []


@given('Repository "{name}" exists')
def provision_repository(context, name):
    r = requests.post(context.gitmesh['create'], data=json.dumps({
        'name': name,
    }))
    assert r.status_code == 201


@when('I create a new "{name}" repository')
def create_repository(context, name):
    r = requests.post(context.gitmesh['create'], data=json.dumps({
        'name': name,
    }))
    assert r.status_code == 201


@when('I delete repository "{name}"')
def delete_repository(context, name):
    listing = requests.get(context.gitmesh['list']).json()
    repos = [repo for repo in listing['repositories'] if repo['name'] == name]
    assert len(repos) == 1
    r = requests.delete(repos[0]['delete'])
    assert r.status_code == 200


@when('I check the repository listing')
def list_repositories(context):
    pass


@then('I should see "{name}" in the repository listing')
def repository_exists(context, name):
    listing = requests.get(context.gitmesh['list']).json()
    assert name in {repo['name'] for repo in listing['repositories']}


@then('I should not see "{name}" in the repository listing')
def repository_does_not_exist(context, name):
    listing = requests.get(context.gitmesh['list']).json()
    assert name not in {repo['name'] for repo in listing['repositories']}
