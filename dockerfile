FROM python:3.10

WORKDIR /app

COPY . /app

 COPY requirements.txt ./
 RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["python", "-u", "main.py"]