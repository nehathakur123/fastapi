FROM python:3.10-alpine3.18

COPY requirements.txt .

RUN pip install --upgrade -r requirements.txt