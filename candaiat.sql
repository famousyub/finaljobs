 CREATE TABLE EMPLOYEE(
   username varchar(20) NOT NULL,

   skills text ,

   id INT PRIMARY KEY AUTO_INCREMENT,

   
);

CREATE TABLE candidates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    skills TEXT
);

CREATE TABLE job_offers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100),
    required_skills TEXT
);
