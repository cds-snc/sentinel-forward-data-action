FROM python:latest@sha256:68d0775234842868248bfe185eece56e725d3cb195f511a21233d0f564dee501

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
