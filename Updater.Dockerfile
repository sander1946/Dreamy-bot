FROM ubuntu:22.04

# set the working directory
WORKDIR /dreamy-bot

# Update the package list
RUN ["apt-get", "update"]

# Install git
RUN apt-get install git -y

# Run the bot
CMD ["git", "pull"]
