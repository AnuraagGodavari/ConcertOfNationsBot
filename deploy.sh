#!/bin/bash

# Update repos
sudo apt update

# Do full upgrade of system
sudo apt full-upgrade -y

# Remove leftover packages and purge configs
sudo apt autoremove
#sudo apt autoremove -y --purge

#Declare text which defines the nationsbot service
pwd=`pwd`
nationsbot="[Unit]
Description=NationsBot Discord Bot
After=multi-user.target

[Service]
Type=simple
Restart=always

ExecStart=/home/anuraag/miniconda3/envs/env_nationsbot/bin/python3 /home/anuraag/DiscordBots/NationsBot/NationsBot

[Install]
WantedBy=multi-user.target"

echo "$nationsbot" > nationsbot.service

sudo cp nationsbot.service /etc/systemd/system/
sudo systemctl start nationsbot.service
sudo systemctl enable nationsbot.service
rm nationsbot.service
