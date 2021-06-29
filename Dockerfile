FROM python:3.9.5-alpine

RUN apk add --no-cache --update build-base gcc libc-dev linux-headers pcre-dev postgresql-dev postgresql-libs su-exec curl

ENV VIRTUAL_ENV=/app
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python3 -m pip install --upgrade pip

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    apk --purge del build-base gcc linux-headers postgresql-dev

EXPOSE 5000

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]

WORKDIR /app/server
COPY server/uwsgi.ini .
COPY server/wsgi.py .
# Copy the antibodyapi directory and all contents
ADD server/antibodyapi antibodyapi

CMD [ "uwsgi", "--ini", "/app/server/uwsgi.ini" ]
