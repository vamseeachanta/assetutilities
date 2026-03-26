USE `krishna-d`;

CREATE TABLE programTestLog(
        ID int AUTO_INCREMENT NOT NULL,
		ProgramName CHAR(50),
		DateTime timestamp,
		FileObjects	TEXT,
		Inputs	TEXT,
		Outputs	TEXT,
		ComparisonWithSuperseded	TEXT,
		AutomatedTestResult TINYINT,
		ManualTestResult TINYINT,
		StatusID TINYINT,
        PRIMARY KEY (ID)
)
