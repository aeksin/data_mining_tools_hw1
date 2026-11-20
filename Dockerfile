FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc make
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY matching.py Makefile matching.c matching_aarch64.S ./
RUN make

CMD ["python", "matching.py"]
