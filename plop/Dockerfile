FROM python:3.13.5-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Command to run the application
CMD ["python", "src/main.py"]