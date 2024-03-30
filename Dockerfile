FROM python:latest@sha256:19973e1796237522ed1fcc1357c766770b47dc15854eafdda055b65953fe5ec1

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
