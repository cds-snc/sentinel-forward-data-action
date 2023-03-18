FROM python:latest@sha256:0d753a7365274cef746b34dde9b4aaa27644f64e1567ed8f40ccd191ac4bd530

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
