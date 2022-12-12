FROM python:3

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the code to the working directory
COPY . .

# Run the bot
CMD ["python", "init.py"]