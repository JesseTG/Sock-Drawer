FROM tiangolo/uwsgi-nginx-flask:python3.7

ARG WORKDIR
ENV WORKDIR="${WORKDIR:-/app}" 

ENV FLASK_APP ${WORKDIR}/main.py
ENV FLASK_DEBUG 0

COPY . ${WORKDIR}

EXPOSE 80 443

RUN "${WORKDIR}/provision.sh"
