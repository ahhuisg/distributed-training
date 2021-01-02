FROM python:3.7

RUN mkdir /app
WORKDIR /app
ADD . /app/
RUN pip install -r requirements.txt

ENV PYTHONPATH /app

EXPOSE 5000
CMD ["python", "-u", "/app/server.py"]
