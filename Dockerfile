FROM python:latest@sha256:6b85854518f812d94cf2dfee2386df85b9cb78835a872d4769b4335f584c43ba

WORKDIR /app

ENV PYTHONPATH /app

COPY src/requirements.txt /app

RUN pip install -r /app/requirements.txt

ADD src /app

COPY . /app

CMD ["python", "/app/src/action.py"]
