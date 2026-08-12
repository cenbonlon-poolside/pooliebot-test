#!/bin/bash
# Run these commands to push to GitHub

# 1. Create a GitHub repository at github.com/new
#    Name: poolie-discord-bot

# 2. Initialize and push
git init
git add .
git commit -m "Initial commit: Poolie Discord bot with Laguna S 2.1"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/poolie-discord-bot.git
git push -u origin main

echo "Replace YOUR_USERNAME with your GitHub username"
echo "Then run: git push -u origin main"
