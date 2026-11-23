USE `krishna-d`;

CREATE TABLE projectAssets(
        ID int AUTO_INCREMENT NOT NULL,
		Project CHAR(50),
		AssetName CHAR(50),
		AssetType CHAR(50),
		Data	TEXT,
        PRIMARY KEY (ID)
)
