# Use Python 3.11
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Start Gunicorn with Eventlet
CMD ["gunicorn", "app:app", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:10000"]
