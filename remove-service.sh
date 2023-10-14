#!/bin/bash

#Disable the systemd service
sudo systemctl stop nationsbot.service
sudo systemctl disable nationsbot.service

#Remove the docker image
sudo docker system prune -a

#Remove the systemd service
sudo rm /etc/systemd/system/nationsbot.service

sudo systemctl daemon-reload
sudo systemctl reset-failed

echo "Removed nationsbot.service"

