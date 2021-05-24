FROM python:3.9.5-alpine

RUN apk add --no-cache --update build-base postgresql-dev postgresql-libs

ENV VIRTUAL_ENV=/app
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

ARG DEVELOPMENT
RUN if [ -z $DEVELOPMENT ] ; then apk --purge del build-base postgresql-dev ; fi

WORKDIR /app/server
COPY server/ontologyapi .

CMD ["flask", "run", "--host=0.0.0.0"]
