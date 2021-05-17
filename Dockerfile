FROM python:3.9.5-alpine

ENV VIRTUAL_ENV=/app
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app/server
COPY server/app.py .

ARG FLASK_ENV
ENV FLASK_ENV=$FLASK_ENV
CMD ["flask", "run", "--host=0.0.0.0"]
