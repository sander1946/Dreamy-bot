FROM ubuntu:22.04

# set the working directory
WORKDIR /dreamy-bot

# Update the package list
RUN ["apt-get", "update"]

# Install git
RUN apt-get install git -y

RUN git config --global --add safe.directory /dreamy-bot

# Run the bot
CMD ["git", "pull"]
