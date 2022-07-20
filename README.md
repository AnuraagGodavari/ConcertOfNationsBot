# NationsBot
A discord bot meant to run a grand strategy roleplaying game by handling economics, resources, building, population etc.

## Features
* Allows users to play as a "nation", which includes such things as owned territories, buildings, resources, etc.
* Players can build their economy in ways such as taxing their population, mining resources and building buildings.

## How to run
Python Libraries:
* Discord.py: A python wrapper for the Discord API used to make the bot itself
* dotenv: A python library which allows us to declare environment variables (ex. the bot's token, which is used to authenticate the bot and must remain secret)
* mysql-connector: A python library which allows us to use the relational database MySQL and its forks (i.e. MariaDB) to store information.