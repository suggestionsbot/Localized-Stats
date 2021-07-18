FROM python:3.9.5-slim
COPY . /stats
WORKDIR stats
RUN pip3 install -r requirements.txt

CMD python3 main.py