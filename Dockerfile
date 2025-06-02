# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1 # Prevents python from writing .pyc files to disc
ENV FLASK_APP=webapp/app.py
ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_DEBUG=1 # Optional: enable debug mode, already in app.py's app.run for now

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the webapp directory into the container at /app
COPY ./webapp ./webapp

# Expose port 5000 (the port Flask will run on)
EXPOSE 5000

# Define the command to run the application
CMD ["flask", "run"]
