FROM python:latest

WORKDIR /src

ENV PYTHONPATH /src

COPY requirements.txt . 

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "action.py"]
