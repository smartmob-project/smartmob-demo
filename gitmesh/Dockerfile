# -*- coding: utf-8 -*-

# Docker compose file should provide:
# - GITMESH_LOGGIN_ENDPOINT

FROM python:3.5

# Install packages (from source).
RUN git clone https://github.com/smartmob-project/gitmesh.git
RUN pip install ./gitmesh
RUN git clone https://github.com/smartmob-project/gitmesh-deploy.git
RUN pip install ./gitmesh-deploy

# Configure gitmesh-deploy plug-in.
ENV GITMESH_DEPLOY_STORAGE "http://fileserver/storage/"
ENV GITMESH_DEPLOY_SMARTMOB_AGENT "http://smartmob-agent/"
ENV GITMESH_DEPLOY_SMARTMOB_APP "myapp"

# Configure path to Git repositories.
RUN mkdir /gitmesh-repositories
WORKDIR /gitmesh-repositories

EXPOSE 80

CMD python -m gitmesh --log-format=json serve --port=80
