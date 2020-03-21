#!/usr/bin/env python3
import sqlite3
from pathlib import Path


class CLI:

    def __init__(self):
        Path("build/").mkdir(exist_ok=True)
        self.init_db()
        self.populate_db()

    def init_db(self):

        self.conn = sqlite3.connect("build/database.db")
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS vietnamese")

        cursor.execute("CREATE TABLE vietnamese ("
                       "rowid INTEGER NOT NULL PRIMARY KEY, "
                       "word TEXT NOT NULL UNIQUE, "
                       "definition TEXT NOT NULL)")

        cursor.execute("CREATE INDEX index_vietnamese_word "
                       "ON vietnamese (word)")

        cursor.close()

    def populate_db(self):
        """ Parses the vnedict text file, and populates the cedict database
            with the relevant fields. """

        cursor = self.conn.cursor()

        numberOfEntry = 0

        with open(file="build/vnedict.txt", mode="r", encoding="utf-8") as file:
            for line in file:
                if line[0] == "#":
                    continue

                word, definition = line.split(":")

                numberOfEntry += 1

                cursor.execute("INSERT INTO vietnamese (rowid, word, definition) "
                               "VALUES (?,?,?) ",
                               (numberOfEntry, word, definition))

        cursor.close()
        self.conn.commit()


CLI()
