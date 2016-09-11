# -*- coding: utf-8 -*-

FROM fluent/fluentd

COPY fluent.conf /fluentd/etc/fluent.conf

EXPOSE 24224
EXPOSE 8888

RUN gem install fluent-plugin-elasticsearch
