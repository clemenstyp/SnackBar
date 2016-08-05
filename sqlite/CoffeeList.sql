PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE coffeelist (id integer primary key, name text, nCoffee int);
INSERT INTO "coffeelist" VALUES(1,'Lennart Duschek',8);
INSERT INTO "coffeelist" VALUES(2,'Jan Oliver Oelerich',1);
INSERT INTO "coffeelist" VALUES(3,'Lukas Nattermann',2);
COMMIT;
