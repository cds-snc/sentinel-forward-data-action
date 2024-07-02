FROM python:latest@sha256:2eedc86b81f2336841f4eed06dff14937d37ec172eec655434fd478eacb1ea49

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
