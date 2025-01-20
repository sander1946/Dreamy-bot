FROM python:3.13-slim-bullseye

# Set the working directory
WORKDIR /Bot

# copy the requirements file
COPY requirements.txt .

# Install the requirements
RUN pip install -r requirements.txt

# Copy the rest of the files
COPY /Bot .

# Run the bot
CMD ["python", "main.py"]