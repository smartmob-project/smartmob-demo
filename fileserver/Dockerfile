# -*- coding: utf-8 -*-

# Docker compose file should provide:
# - SMARTMOB_LOGGING_ENDPOINT

FROM python:3.5

# Install packages (from source).
RUN git clone https://github.com/smartmob-project/smartmob-filestore.git
RUN pip install ./smartmob-filestore

EXPOSE 80

CMD python -m smartmob_filestore --port=80
