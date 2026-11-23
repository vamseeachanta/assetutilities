USE `krishna-d`;

CREATE TABLE serviceAssets(
        ID int AUTO_INCREMENT NOT NULL,
		Operator CHAR(50),
		AssetName CHAR(50),
		AssetType CHAR(50),
		Data	TEXT,
        PRIMARY KEY (ID)
)
