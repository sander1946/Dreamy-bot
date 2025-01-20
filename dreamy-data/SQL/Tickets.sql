DROP DATABASE IF EXISTS `Server_data`;
CREATE database `Server_data`;
USE `Server_data`;
CREATE TABLE open_tickets  (
	id INT AUTO_INCREMENT PRIMARY KEY,
    user_id bigint NOT NULL,
    channel_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE rule_channels (
	id INT AUTO_INCREMENT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    creator_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE rules_accepted (
	id INT AUTO_INCREMENT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL
);
CREATE TABLE reminders (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user_id BIGINT NOT NULL,
	reminder_id BIGINT NOT NULL,
	begin_event_time DATETIME NOT NULL,
	reminder_time DATETIME NOT NULL,
	end_event_time DATETIME,
	end_reminder_time DATETIME,
	channel_id BIGINT,
	message_id BIGINT
);
CREATE TABLE reminder_participants (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user_id BIGINT NOT NULL,
	reminder_id BIGINT NOT NULL,
	subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);