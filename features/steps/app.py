# -*- coding: utf-8 -*-


import os
import os.path
import requests
import shutil
import time

from behave import given, then
from subprocess import check_output, CalledProcessError, STDOUT


def copytree(src, dst):
    """Variant of shutil.copytree() that works when ``dst`` already exists."""

    print('Copying tree "%s".' % src)
    assert os.path.isdir(dst)
    for name in os.listdir(src):
        srcpath = os.path.join(src, name)
        dstpath = os.path.join(dst, name)
        if os.path.isdir(srcpath):
            os.mkdir(dstpath)
            copytree(srcpath, dstpath)
        else:
            print('Copying file "%s".' % dstpath)
            shutil.copyfile(srcpath, dstpath)


@given('Application "{name}" exists')
def provision_application(context, name):
    pass


@given('I submit the "{name}" sample')
def submit_sample(context, name):
    copytree(src=os.path.join(context.test_root, 'samples', name), dst='.')
    try:
        output = check_output(['git', 'add', '.'], stderr=STDOUT)
    except CalledProcessError as e:
        output = e.output
        raise
    finally:
        print(output)
    try:
        output = check_output(['git', 'commit', '-m', 'Adds sample.'])
    except CalledProcessError as e:
        output = e.output
        raise
    finally:
        print(output)


@then('Application "{name}" should be deployed')
def check_deployment(context, name):
    processes = requests.get(context.smartmob_agent['list']).json()
    processes = processes['processes']
    print(processes)
    assert len(processes) == 1
    p = processes[0]
    assert p['app'] == 'myapp'
    assert p['slug'] == 'myapp.1'
    while p['state'] in ('pending', 'downloading', 'unpacking'):
        time.sleep(0.1)
        p = requests.get(p['details']).json()
    assert p['state'] == 'processing'
