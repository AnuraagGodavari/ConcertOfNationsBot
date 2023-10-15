# NationsBot
 A discord bot meant to run a grand strategy roleplaying game by handling economics, resources, building, population etc.

## Features

* Allows users to play as a "nation", which includes such things as owned territories, buildings, resources, etc.
* Admins can set up a game for a server by choosing a gamerule (the ruleset, including available buildings and settings) as well as a base worldmap.
* Nations own territories in the worldmap and can build buildings in them in order to mine or produce resources.
* Territories also have populations, which can be taxed and recruited as units in a military force.
* Admins can manually do anything a nation can as well as spawn resources, buildings or units for purposes of RP events.

## Dependencies
Python Libraries:
* discord.py: A python wrapper for the Discord API used to make the bot itself
* dotenv: A python library which allows us to declare environment variables (ex. the bot's token, which is used to authenticate the bot and must remain secret)
* mysql-connector: A python library which allows us to use the relational database MySQL and its forks (i.e. MariaDB) to store information.
* imgurpython: A python wrapper for the imgur API, used to upload and retrieve images.
* pillow: A python library for generating images.
Other:
* MariaDB: The database solution used by this project.
* Docker: a containerization solution. On linux, the packages required are docker and docker.io.
* Server: Currently, deployment is known to work on Ubuntu and Raspbian. The deploy script uses commands for a debian-based system.

## Setup and Deployment
For the database, simply run schema.sql.
Once the dependencies are met, run the bash script deploy.sh. This will create a file called .env. Fill it out with the necessary information, including for connecting to the database, the discord bot token, and the information for using the imgur API.

## TBD
Feel free to take a look at the issues and milestones for planned features and fixes!