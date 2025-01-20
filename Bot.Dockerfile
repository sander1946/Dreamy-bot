FROM python:3.13-slim-bullseye

# Set the working directory
WORKDIR /dreamy-bot/Bot

# copy the requirements file
COPY requirements.txt .

# Install the requirements
RUN pip install -r requirements.txt

# Run the bot
CMD ["python", "main.py"]