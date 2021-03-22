# Container image that runs your code
FROM python:alpine

RUN pip install pyyaml requests
COPY changelogger.py /changelogger.py

ENV SRC_PATH /github/workspace
RUN mkdir -p $SRC_PATH

VOLUME [ "$SRC_PATH" ]
WORKDIR $SRC_PATH

ENTRYPOINT [ "python", "/changelogger.py" ]
