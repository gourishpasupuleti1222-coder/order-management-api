FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY create_admin.py /app/create_admin.py

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]