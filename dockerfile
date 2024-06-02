FROM python:3.10

WORKDIR /app

COPY . /app

 COPY requirements.txt ./
 RUN pip install --no-cache-dir -r requirements.txt


CMD ["python", "-u", "main.py"]