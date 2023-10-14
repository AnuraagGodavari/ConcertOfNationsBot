#!/bin/bash

# Update repos
sudo apt update

# Do full upgrade of system
sudo apt full-upgrade -y

# Remove leftover packages and purge configs
sudo apt autoremove
#sudo apt autoremove -y --purge

#Create .env file if not exists
if [ ! -f ".env" ] ; then
    env="
    TOKEN=

    DB_USER=
    DB_PASS=
    DB_HOST=
    DB_DATABASE=
    DB_PORT="

    echo "$env" > .env

    echo "Please fill out the information in the newly created .env file before proceeding."

    exit

fi

#Build the docker image
sudo docker build -t nationsbot .

#Declare text which defines the nationsbot service
pwd=`pwd`
nationsbot="[Unit]
Description=Concert Of Nations Discord Bot
After=multi-user.target

[Service]
Type=simple
Restart=always

ExecStart=/usr/bin/docker run --name nationsbot --rm nationsbot
ExecStop=-/usr/bin/docker stop nationsbot

[Install]
WantedBy=multi-user.target"

#Create the service
echo "$nationsbot" > nationsbot.service

sudo cp nationsbot.service /etc/systemd/system/
sudo systemctl start nationsbot.service
sudo systemctl enable nationsbot.service

sudo systemctl daemon-reload

rm nationsbot.service

echo "Successfully created nationsbot service!"
