# Container image that runs your code
FROM python:alpine

RUN pip install pyyaml requests
COPY changelogger.py /changelogger.py

ENV INPUT_OWNER=
ENV INPUT_REPO=
ENV INPUT_OUTPUT-FILE=CHANGELOG.md
ENV INPUT_CONFIG-FILE=changelog.yml
ENV INPUT_GITHUB-TOKEN=
ENV INPUT_PREVIOUS-TAG=
ENV INPUT_CURRENT-TAG=
ENV INPUT_GITHUB-SITE=
ENV INPUT_GITHUB-API=

ENV SRC_PATH /usr/local/src/your-app
RUN mkdir -p $SRC_PATH

VOLUME [ "$SRC_PATH" ]
WORKDIR $SRC_PATH

ENTRYPOINT [ "python", "/changelogger.py", "--github-api ${INPUT_GITHUB-API} --github-site ${INPUT_GITHUB-SITE} --github-token ${INPUT_GITHUB-TOKEN}", "--output-file ${INPUT_OUTPUT-FILE} --config-file ${INPUT_CONFIG-FILE}" ]
