FROM python:3.12-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /app/
COPY sql/03_reportes.sql /app/sql/03_reportes.sql
EXPOSE 5000
CMD ["python", "app.py"]
