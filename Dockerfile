FROM python:latest@sha256:02808bfd640d6fd360c30abc4261ad91aacacd9494f9ba4e5dcb0b8650661cf5

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
