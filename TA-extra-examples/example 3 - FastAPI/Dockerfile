FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY example_3_2-Full.py .

# Create a volume mount point for the database
VOLUME ["/app/data"]

# Change SQLite database path to the volume
ENV SQLITE_DB_PATH=/app/data/test.db

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "example_3_2-Full:app", "--host", "0.0.0.0", "--port", "8000"]
