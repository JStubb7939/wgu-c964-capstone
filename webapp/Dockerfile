# Use official Python base image
FROM python:3.14-slim

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY version.txt .
COPY system_prompt.txt .
COPY templates/ templates/
COPY static/ static/

# Expose port 8000 for Azure Container App
EXPOSE 8000

# Run the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
