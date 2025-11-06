# Use official Python base image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY version.txt .
COPY templates/ templates/
COPY static/ static/

# Expose port 8000 for Azure App Service
EXPOSE 8000

# Run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
