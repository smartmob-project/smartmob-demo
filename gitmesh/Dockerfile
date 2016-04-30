# -*- coding: utf-8 -*-

FROM python:3.5

RUN pip install gitmesh==0.1.0
RUN pip install aiohttp==0.21.5
RUN pip install voluptuous==0.8.11

RUN mkdir /gitmesh
WORKDIR /gitmesh

EXPOSE 80
CMD python -m gitmesh serve --port=80
