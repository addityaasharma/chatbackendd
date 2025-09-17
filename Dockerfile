# Use Python 3.13
FROM python:3.13-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port (Render provides $PORT)
ENV PORT 5000
EXPOSE $PORT

# Use Gunicorn with Gevent for production
CMD ["gunicorn", "-k", "gevent", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
