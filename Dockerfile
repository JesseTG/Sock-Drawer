FROM tiangolo/uwsgi-nginx-flask:python3.7-alpine3.7

ARG WORKDIR
ENV WORKDIR="${WORKDIR:-/app}" 

ENV FLASK_APP ${WORKDIR}/main.py
ENV FLASK_DEBUG 0

#RUN addgroup -S ${APP_USER} && adduser -S -G ${APP_USER} ${APP_USER}
RUN apk update && apk add --no-cache gcc g++ libffi-dev
#RUN apt-get update && apt-get install gcc g++ libffi-dev

COPY . ${WORKDIR}

RUN ${WORKDIR}/provision.sh

EXPOSE 80 443
