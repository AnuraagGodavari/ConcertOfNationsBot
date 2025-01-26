USE ConcertOfNations;

ALTER TABLE `WorldMaps` RENAME `GameWorldMaps`;

CREATE TABLE IF NOT EXISTS `WorldMaps` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `world_id` BIGINT UNSIGNED NOT NULL,
    `version` INT UNSIGNED NOT NULL,
    `filename` VARCHAR(128),
    `link` VARCHAR(128) UNIQUE,
    `created` timestamp NOT NULL DEFAULT current_timestamp(),
    PRIMARY KEY (`id`),
    CONSTRAINT `WorldMaps_ibfk_1` FOREIGN KEY (`world_id`) REFERENCES `Worlds` (`id`),
    UNIQUE(`world_id`, `version`)
);