FROM python:3.11.8
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
COPY bot.py bot.py
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
