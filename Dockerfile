FROM python:latest

WORKDIR /app

ENV PYTHONPATH /app

RUN pwd && ls

COPY src/requirements.txt /app

RUN pwd && ls

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

RUN pwd && ls

CMD ["python", "/app/src/action.py"]
