FROM python:3.7.0-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /src/api

CMD ["gunicorn -w 1 --threads 12", "--reload",  "main:app"]
