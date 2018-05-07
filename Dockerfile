FROM tiangolo/uwsgi-nginx-flask:python3.6

ENV WORKDIR /app 
ENV FLASK_APP ${WORKDIR}/main.py
ENV FLASK_DEBUG 0

#RUN addgroup -S ${APP_USER} && adduser -S -G ${APP_USER} ${APP_USER}
#RUN apk update && apk add --no-cache gcc g++ libffi-dev
RUN apt-get update && apt-get install gcc g++ libffi-dev

COPY . ${WORKDIR}

RUN pip3 install --no-cache-dir --requirement requirements/prod.txt

EXPOSE 80 443
