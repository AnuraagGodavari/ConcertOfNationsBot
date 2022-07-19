#!/bin/bash

# Update repos
sudo apt update

# Do full upgrade of system
sudo apt full-upgrade -y

# Remove leftover packages and purge configs
sudo apt autoremove
#sudo apt autoremove -y --purge

#Declare text which defines the lilbuddy service
pwd=`pwd`
lilbuddy="[Unit]
Description=Lil' Buddy Discord Bot
After=multi-user.target

[Service]
Type=simple
Restart=always

ExecStart=/home/anuraag/miniconda3/envs/env_LilBuddy/bin/python3 /home/anuraag/DiscordBots/Lil-Buddy/Lil-Buddy

[Install]
WantedBy=multi-user.target"

echo "$lilbuddy" > lilbuddy.service

sudo cp lilbuddy.service /etc/systemd/system/
sudo systemctl start lilbuddy.service
sudo systemctl enable lilbuddy.service
rm lilbuddy.service
