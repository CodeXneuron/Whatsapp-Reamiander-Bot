# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for the Flask application
EXPOSE 5000

# Define environment variables from the .env file
# This is a secure way to pass secrets to the container
# Note: For production, use Cloud Secret Manager instead of a .env file
# This is a temporary way for this guide
ARG TWILIO_ACCOUNT_SID
ARG TWILIO_AUTH_TOKEN
ARG TWILIO_WHATSAPP_NUMBER
ARG FIREBASE_CONFIG

ENV TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
ENV TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
ENV TWILIO_WHATSAPP_NUMBER=${TWILIO_WHATSAPP_NUMBER}
ENV FIREBASE_CONFIG=${FIREBASE_CONFIG}

# Run the Flask app
CMD ["python", "app.py"]

