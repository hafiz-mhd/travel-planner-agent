-- Travel Planner Agent – MySQL Schema
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS travel_planner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE travel_planner;

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    preferences     VARCHAR(1000),
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Trips ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trips (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    title           VARCHAR(500) NOT NULL,
    destination     VARCHAR(500) NOT NULL,
    start_date      DATE         NOT NULL,
    end_date        DATE         NOT NULL,
    budget_min      DECIMAL(10,2),
    budget_max      DECIMAL(10,2),
    num_travelers   TINYINT UNSIGNED NOT NULL DEFAULT 1,
    interests       VARCHAR(500),
    raw_itinerary   LONGTEXT,           -- full JSON blob from LLM
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_trips_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_trips_user (user_id),
    INDEX idx_trips_dates (start_date, end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Itinerary Items ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS itinerary_items (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    trip_id         INT UNSIGNED NOT NULL,
    day_number      TINYINT UNSIGNED NOT NULL,
    period          ENUM('morning','afternoon','evening') NOT NULL,
    activity        VARCHAR(1000) NOT NULL,
    location        VARCHAR(500),
    description     TEXT,
    estimated_cost  DECIMAL(8,2),
    weather_risk    ENUM('low','medium','high') DEFAULT 'low',
    tips            TEXT,
    CONSTRAINT fk_items_trip FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    INDEX idx_items_trip_day (trip_id, day_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
