# Import libraries
import requests
import xml.etree.ElementTree as ET
import sys
import sqlite3
import time
from csv import reader
from os import walk
import itertools
import gzip
import io


# Start time - Just to count how much the script lasts
start_time = time.time()

# Name of the database
DB_FILE = "database/All_META_OA.db"

# Connect to the SQLite database
# If name not found, it will create a new database
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()


c.execute('''DROP TABLE IF EXISTS Citations''')
c.execute('''CREATE TABLE "Citations" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Introduction''')
c.execute('''CREATE TABLE "Citations_Introduction" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Methods''')
c.execute('''CREATE TABLE "Citations_Methods" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,                
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Results''')
c.execute('''CREATE TABLE "Citations_Results" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

# Create Citations for the introduction section table
c.execute('''DROP TABLE IF EXISTS Citations_Discussion''')
c.execute('''CREATE TABLE "Citations_Discussion" (
                "id1"	TEXT NOT NULL,
                "id2"	TEXT NOT NULL,
                "n_citations" INTEGER,
                "year" INTEGER,
                FOREIGN KEY("id1") REFERENCES "Publications"("id"),
                FOREIGN KEY("id2") REFERENCES "Publications"("id")
            );''')

conn.commit()

c.close()


