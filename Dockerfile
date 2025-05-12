FROM python:latest@sha256:3abe339a3bc81ffabcecf9393445594124de6420b3cfddf248c52b1115218f04

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
