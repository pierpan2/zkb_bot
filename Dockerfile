# Use the official Python image from the Docker Hub
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the contents of the local directory to the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install additional packages
RUN apt-get update && apt-get install -y fonts-wqy-zenhei

# Command to run your bot
CMD ["python3.10", "bot.py"]
