FROM python:3.7.0-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /src/get_transaction

CMD ["gunicorn", "--reload", "-c", "config.py", "main:app"]