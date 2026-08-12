#!/bin/bash
# Run this on your EC2 instance after launching

# Update and install Python
sudo dnf update -y
sudo dnf install python3-pip git -y

# Clone or copy your bot
# git clone <your-repo> poolie
# OR upload the files via SCP

# Setup
cd poolie
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run (or use systemd for persistence)
python bot.py
