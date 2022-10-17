/*
*/
DROP DATABASE IF EXISTS ConcertOfNations;

CREATE DATABASE IF NOT EXISTS ConcertOfNations DEFAULT CHARACTER SET = 'utf8mb4';

USE ConcertOfNations;

CREATE TABLE IF NOT EXISTS `Savegames` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `server_id` BIGINT UNSIGNED NOT NULL UNIQUE,
    `savefile` VARCHAR(64) NOT NULL UNIQUE,
    `worldfile` VARCHAR(64) NOT NULL,
    `gamerulefile` VARCHAR(64) NOT NULL,
    `created` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `Players` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `discord_id` BIGINT UNSIGNED NOT NULL UNIQUE,
    `created` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `Roles` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `discord_id` BIGINT UNSIGNED NOT NULL UNIQUE,
    `name` VARCHAR(32) NOT NULL,
    `desc` VARCHAR(128),
    PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `PlayerGames` (
    `player_id` BIGINT UNSIGNED NOT NULL,
    `game_id` BIGINT UNSIGNED NOT NULL,
    `role_id` BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (`player_id`, `game_id`),
    CONSTRAINT `PlayerGames_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `Players` (`id`),
    CONSTRAINT `PlayerGames_ibfk_2` FOREIGN KEY (`game_id`) REFERENCES `Savegames` (`id`),
    CONSTRAINT `PlayerGames_ibfk_3` FOREIGN KEY (`role_id`) REFERENCES `Roles` (`id`)
);

CREATE TABLE IF NOT EXISTS `SavefileDownloads` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `game_id` BIGINT UNSIGNED NOT NULL,
    `player_id` BIGINT UNSIGNED NOT NULL,
    `created` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`),
    CONSTRAINT `SavefileDownloads_ibfk_1` FOREIGN KEY (`game_id`) REFERENCES `Savegames` (`id`),
    CONSTRAINT `SavefileDownloads_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `Players` (`id`)
);

CREATE TABLE IF NOT EXISTS `NewTurns` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `game_id` BIGINT UNSIGNED NOT NULL,
    `turn_no` INT UNSIGNED NOT NULL,
    `date` VARCHAR(16),
    `created` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`),
    CONSTRAINT `NewTurns_ibfk_1` FOREIGN KEY (`game_id`) REFERENCES `Savegames` (`id`)
);

CREATE TABLE IF NOT EXISTS `MapImages` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `link` VARCHAR(48),
    `conditions` VARCHAR(256),
    `created` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`)
);
