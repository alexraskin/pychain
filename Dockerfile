FROM python:3.9-alpine

WORKDIR /app

ADD requirements.txt /app
RUN cd /app && \
    pip install -r requirements.txt

ADD blockchain.py /app

EXPOSE 5000

CMD ["python", "blockchain.py", "--port", "5000"]