FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the Flask application with Gunicorn (production ready)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "antifraud:app"]