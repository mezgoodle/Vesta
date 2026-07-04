FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Cloud Run sets the PORT environment variable
ENV PORT 8080

# Run the bot
CMD ["python", "bot.py"]
