# Container image that runs your code
FROM python:alpine

RUN pip install pyyaml requests
COPY changelogger.py /changelogger.py

ENV OUTPUT-FILE=CHANGELOG.md
ENV CONFIG-FILE=changelog.yml
ENV GITHUB-TOKEN=
ENV GITHUB-SITE=
ENV GITHUB-API=

ENV SRC_PATH /usr/local/src/your-app
RUN mkdir -p $SRC_PATH

VOLUME [ "$SRC_PATH" ]
WORKDIR $SRC_PATH

ENTRYPOINT [ "python", "/changelogger.py", "--github-api ${GITHUB-API} --github-site ${GITHUB-SITE} --github-token ${GITHUB-TOKEN}", "--output-file ${OUTPUT-FILE} --config-file ${CONFIG-FILE}" ]
