FROM python:3.9
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY random_rank.py .
COPY youtube_links.txt .
COPY templates/ templates/

ENV FLASK_APP=random_rank.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--workers=4", "--timeout=120", "--bind=0.0.0.0:5000", "--access-logfile=-", "--error-logfile=-", "random_rank:app"]
