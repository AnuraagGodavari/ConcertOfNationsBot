#!/bin/bash

# Update repos
sudo apt update

# Do full upgrade of system
sudo apt full-upgrade -y

# Remove leftover packages and purge configs
sudo apt autoremove
#sudo apt autoremove -y --purge

sudo apt install docker docker.io

#Create .env file if not exists
if [ ! -f ".env" ] ; then
    env="
    TOKEN=

    TESTSUITE_SCRIPT=
    TESTSUITE_SCRIPT_BOT=

    TEST_CHANNEL_ID=

    DB_USER=
    DB_PASS=
    DB_HOST=
    DB_DATABASE=
    DB_PORT=

    IMGUR_CLIENT_ID=
    IMGUR_CLIENT_SECRET="

    echo "$env" > .env

    echo "Please fill out the information in the newly created .env file before proceeding."

    exit

fi

#Create folders if they do not exist

declare -a botdirs=("Assets" "Gamerule" "Logs" "Savegames" "Worlds")

for i in "${botdirs[@]}"
do
	if [ ! -d "$i" ] ; then
		mkdir $i
	fi	
done


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

ExecStart=/usr/bin/docker run \
        -v $(pwd)/Assets:/NationsBot-App/Assets \
        -v $(pwd)/Gamerule:/NationsBot-App/Gamerule \
        -v $(pwd)/Logs:/NationsBot-App/Logs \
        -v $(pwd)/Savegames:/NationsBot-App/Savegames \
        -v $(pwd)/Worlds:/NationsBot-App/Worlds \
        --name nationsbot --rm nationsbot \

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
