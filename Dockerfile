FROM python:3.10.5-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]

VOLUME [ "/app/config.py" ]