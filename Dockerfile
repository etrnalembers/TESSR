# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This is done in a separate step to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code
COPY . .

# Make port 3177 available to the world outside this container
EXPOSE 3177

# Define the command to run the application using Gunicorn
# This is a production-ready WSGI server.
# It runs the 'app' object from the 'main.py' file.
CMD ["gunicorn", "--bind", "0.0.0.0:3177", "main:app"]
