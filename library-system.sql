-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 20, 2025 at 02:45 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `library-system`
--

-- --------------------------------------------------------

--
-- Table structure for table `author`
--

CREATE TABLE `author` (
  `authorid` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `status` enum('Enable','Disable') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `author`
--

INSERT INTO `author` (`authorid`, `name`, `status`) VALUES
(1, 'SUDHA MAM', 'Enable'),
(2, 'NASIRA MAM', 'Enable'),
(7, 'BALAJI', 'Enable');

-- --------------------------------------------------------

--
-- Table structure for table `book`
--

CREATE TABLE `book` (
  `bookid` int(10) UNSIGNED NOT NULL,
  `categoryid` int(11) NOT NULL,
  `authorid` int(11) NOT NULL,
  `name` text NOT NULL,
  `picture` varchar(250) NOT NULL,
  `publisherid` int(11) NOT NULL,
  `isbn` varchar(30) NOT NULL,
  `no_of_copy` int(5) NOT NULL,
  `status` enum('Enable','Disable') NOT NULL,
  `added_on` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_on` datetime NOT NULL DEFAULT current_timestamp(),
  `pdf_path` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `book`
--

INSERT INTO `book` (`bookid`, `categoryid`, `authorid`, `name`, `picture`, `publisherid`, `isbn`, `no_of_copy`, `status`, `added_on`, `updated_on`, `pdf_path`) VALUES
(1, 1, 1, 'VB', 'book.jpg', 1, 'BOOKX30N', 1, 'Enable', '2024-12-19 08:22:13', '2025-01-05 19:53:09', 'VB.pdf'),
(2, 1, 2, 'Python', 'book.jpg', 1, 'BOOKTHON', 1, 'Enable', '2024-12-19 17:08:29', '2024-12-19 17:08:29', 'Python.pdf'),
(11, 1, 1, 'BALAJI', 'book.jpg', 1, 'BOOKSBN', 1, 'Enable', '2025-01-05 20:07:23', '2025-01-05 20:07:23', 'Capstone Project Challenge Format _ ServiceNow Administration….pdf'),
(18, 12, 7, 'CAPSTONE', 'default.jpg', 14, 'sfdjnfyjkd', 2, 'Enable', '2025-01-29 20:32:03', '2025-01-29 20:32:03', 'Capstone Project Challenge Format _ ServiceNow Administration….pdf');

-- --------------------------------------------------------

--
-- Table structure for table `category`
--

CREATE TABLE `category` (
  `categoryid` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `status` enum('Enable','Disable') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `category`
--

INSERT INTO `category` (`categoryid`, `name`, `status`) VALUES
(1, 'PROGRAMMING', 'Enable'),
(12, 'HEALTH', 'Enable');

-- --------------------------------------------------------

--
-- Table structure for table `issued_book`
--

CREATE TABLE `issued_book` (
  `issuebookid` int(11) NOT NULL,
  `bookid` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `issue_date_time` datetime NOT NULL DEFAULT current_timestamp(),
  `expected_return_date` datetime NOT NULL,
  `return_date_time` datetime NOT NULL,
  `status` enum('Issued','Returned','Not Return') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `issued_book`
--

INSERT INTO `issued_book` (`issuebookid`, `bookid`, `userid`, `issue_date_time`, `expected_return_date`, `return_date_time`, `status`) VALUES
(1, 2, 2, '2022-06-12 15:33:45', '2025-02-01 11:00:00', '2025-02-28 12:00:00', 'Returned'),
(3, 1, 2, '2022-06-12 18:46:07', '2024-12-01 10:00:00', '2025-02-01 18:46:14', 'Returned'),
(7, 18, 7, '2025-02-01 08:22:13', '2025-02-01 08:21:49', '2025-02-22 08:22:03', 'Returned'),
(9, 1, 8, '2025-02-28 12:30:07', '2025-02-28 12:29:36', '2025-03-08 12:00:00', 'Issued'),
(10, 2, 1, '2025-02-28 12:30:52', '2025-02-28 12:30:40', '2025-03-22 12:30:44', 'Issued');

-- --------------------------------------------------------

--
-- Table structure for table `publisher`
--

CREATE TABLE `publisher` (
  `publisherid` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `status` enum('Enable','Disable') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `publisher`
--

INSERT INTO `publisher` (`publisherid`, `name`, `status`) VALUES
(1, 'CGAC', 'Enable'),
(14, 'BALAJI', 'Enable');

-- --------------------------------------------------------

--
-- Table structure for table `queries`
--

CREATE TABLE `queries` (
  `id` int(11) NOT NULL,
  `book_request` varchar(255) NOT NULL,
  `description` varchar(1000) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `queries`
--

INSERT INTO `queries` (`id`, `book_request`, `description`) VALUES
(2, 'Harry Potter', 'I want Harry Potter Book'),
(3, 'Great Gatsby', 'I want This');

-- --------------------------------------------------------

--
-- Table structure for table `reviews`
--

CREATE TABLE `reviews` (
  `id` int(11) NOT NULL,
  `user_id` int(10) UNSIGNED NOT NULL,
  `book_id` int(10) UNSIGNED NOT NULL,
  `review` text NOT NULL,
  `rating` int(11) NOT NULL CHECK (`rating` between 1 and 5),
  `created_on` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reviews`
--

INSERT INTO `reviews` (`id`, `user_id`, `book_id`, `review`, `rating`, `created_on`) VALUES
(12, 2, 11, 'really good!!!', 5, '2025-01-28 12:28:39'),
(13, 2, 2, 'bro', 5, '2025-01-28 12:44:24'),
(14, 1, 11, 'awesome', 5, '2025-02-20 03:25:46'),
(15, 2, 18, 'ok', 3, '2025-03-03 06:15:12');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` int(10) UNSIGNED NOT NULL,
  `first_name` varchar(255) DEFAULT NULL,
  `last_name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `password` varchar(64) NOT NULL,
  `role` enum('admin','user') DEFAULT 'admin',
  `profile_pic_url` varchar(255) NOT NULL,
  `reset_token` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `first_name`, `last_name`, `email`, `password`, `role`, `profile_pic_url`, `reset_token`) VALUES
(1, 'BALAJI', 'K', 'balajijojo7@gmail.com', '123', 'admin', '', '2d1779d6-a5bb-422b-ae38-ed7df1c2987a'),
(2, 'USER', 'TEST', 'user@gmail.com', '123', 'user', '', NULL),
(7, 'Karthik', 'j', 'k@gmail.com', '123', 'user', '', ''),
(8, 'DINESH', 'W', 'd@gmail.com', '123', 'user', '', '');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `author`
--
ALTER TABLE `author`
  ADD PRIMARY KEY (`authorid`);

--
-- Indexes for table `book`
--
ALTER TABLE `book`
  ADD PRIMARY KEY (`bookid`);

--
-- Indexes for table `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`categoryid`);

--
-- Indexes for table `issued_book`
--
ALTER TABLE `issued_book`
  ADD PRIMARY KEY (`issuebookid`);

--
-- Indexes for table `publisher`
--
ALTER TABLE `publisher`
  ADD PRIMARY KEY (`publisherid`);

--
-- Indexes for table `queries`
--
ALTER TABLE `queries`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `reviews`
--
ALTER TABLE `reviews`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `book_id` (`book_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `author`
--
ALTER TABLE `author`
  MODIFY `authorid` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `book`
--
ALTER TABLE `book`
  MODIFY `bookid` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `category`
--
ALTER TABLE `category`
  MODIFY `categoryid` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `issued_book`
--
ALTER TABLE `issued_book`
  MODIFY `issuebookid` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `publisher`
--
ALTER TABLE `publisher`
  MODIFY `publisherid` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `queries`
--
ALTER TABLE `queries`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `reviews`
--
ALTER TABLE `reviews`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `reviews`
--
ALTER TABLE `reviews`
  ADD CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`book_id`) REFERENCES `book` (`bookid`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
