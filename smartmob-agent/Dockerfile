# -*- coding: utf-8 -*-

FROM python:3.5

RUN git clone https://github.com/smartmob-project/smartmob-agent.git
RUN pip install ./smartmob-agent

EXPOSE 80

CMD smartmob-agent --port=80
