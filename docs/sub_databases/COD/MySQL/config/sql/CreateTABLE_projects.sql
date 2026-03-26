USE `krishna-d`;

CREATE TABLE projects(
        ID int AUTO_INCREMENT NOT NULL,
		ProjectName CHAR(50),
		Operator CHAR(50),
		Location CHAR(50),
		ProjectType CHAR(50),
		Data	TEXT,
        PRIMARY KEY (ID)
)
