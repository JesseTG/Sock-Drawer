FROM tiangolo/uwsgi-nginx-flask:python3.7

ARG WORKDIR
ENV WORKDIR="${WORKDIR:-/app}" 

ENV FLASK_APP ${WORKDIR}/main.py
ENV FLASK_DEBUG 0

COPY . ${WORKDIR}

# TODO: Open a UNIX socket for logging, and one for communication
RUN "${WORKDIR}/provision.sh"

EXPOSE 80 443

#HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "executable" ]
# some flask command more likely
