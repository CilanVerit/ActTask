# Base image with python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Get requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Flask environment
ENV FLASK_APP=acttask
ENV FLASK_RUN_HOST=0.0.0.0

# Expose port
EXPOSE 5000

# Run application
CMD ["flask", "run"]