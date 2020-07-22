FROM python:3.8

COPY requirements.txt .
RUN pip install -rrequirements.txt

COPY . /var/src/monitoro

WORKDIR /var/src/monitoro
CMD python -m monitoro
