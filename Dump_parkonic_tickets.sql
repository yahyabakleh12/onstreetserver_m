-- MySQL dump 10.13  Distrib 8.0.xx, for Win64 (x86_64)
--
-- Host: localhost    Database: parkonic_tickets
-- ------------------------------------------------------
-- Server version	8.0.xx

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Database structure for database `parkonic_tickets`
--

CREATE DATABASE IF NOT EXISTS `parkonic_tickets`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `parkonic_tickets`;

--
-- Table structure for table `omc_ticket`
--

DROP TABLE IF EXISTS `omc_ticket`;

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `omc_ticket` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `camera_id` int DEFAULT NULL,
  `zone_name` varchar(50) DEFAULT NULL,
  `camera_ip` varchar(45) DEFAULT NULL,
  `zone_region` varchar(50) DEFAULT NULL,
  `spot_number` int DEFAULT NULL,
  `plate_number` varchar(20) DEFAULT NULL,
  `plate_code` varchar(10) DEFAULT NULL,
  `plate_city` varchar(50) DEFAULT NULL,
  `confidence` int DEFAULT NULL,
  `entry_time` datetime DEFAULT NULL,
  `exit_time` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `parkonic_trip_id` int DEFAULT NULL,
  `image_base64` longtext,
  `crop_image_path` varchar(255) DEFAULT NULL,
  `entry_image_path` varchar(255) DEFAULT NULL,
  `exit_image_path` varchar(255) DEFAULT NULL,
  `exit_clip_path` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `process_time_in` datetime DEFAULT NULL,
  `process_time_out` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_camera_time` (`camera_id`,`entry_time`),
  KEY `idx_plate` (`plate_number`,`plate_code`),
  KEY `idx_trip` (`parkonic_trip_id`),
  KEY `idx_zone` (`zone_name`,`zone_region`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ocr_ticket`
--

DROP TABLE IF EXISTS `ocr_ticket`;

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ocr_ticket` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `camera_id` int DEFAULT NULL,
  `zone_name` varchar(50) DEFAULT NULL,
  `camera_ip` varchar(45) DEFAULT NULL,
  `zone_region` varchar(50) DEFAULT NULL,
  `spot_number` int DEFAULT NULL,
  `plate_number` varchar(20) DEFAULT NULL,
  `plate_code` varchar(10) DEFAULT NULL,
  `plate_city` varchar(50) DEFAULT NULL,
  `confidence` int DEFAULT NULL,
  `entry_time` datetime DEFAULT NULL,
  `exit_time` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `parkonic_trip_id` int DEFAULT NULL,
  `image_base64` longtext,
  `crop_image_path` varchar(255) DEFAULT NULL,
  `entry_image_path` varchar(255) DEFAULT NULL,
  `exit_image_path` varchar(255) DEFAULT NULL,
  `exit_clip_path` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `process_time_in` datetime DEFAULT NULL,
  `process_time_out` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_camera_time` (`camera_id`,`entry_time`),
  KEY `idx_plate` (`plate_number`,`plate_code`),
  KEY `idx_trip` (`parkonic_trip_id`),
  KEY `idx_zone` (`zone_name`,`zone_region`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-25 08:09:06
