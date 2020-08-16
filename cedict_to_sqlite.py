#!/usr/bin/env python3
import sqlite3
import gzip
from pathlib import Path
from argparse import ArgumentParser
import requests
from pinyin import convert_pinyin


class CLI:
    """ Very basic command line interface to convert a cedict file to a sqlite
        database. """

    WEB_CEDICT_FILE = ("https://www.mdbg.net/chinese/export/cedict/"
                       "cedict_1_0_ts_utf-8_mdbg.txt.gz")

    def __init__(self):
        self.init_args()
        self.download_cedict()
        self.init_db()
        self.populate_db()

    def init_args(self):
        """ Inits the argument parser. """

        parser = ArgumentParser(
            description="Converts cedict to a sqlite database.")
        parser.add_argument("--enable-tone-accents",
                            dest="enable_tone_accents",
                            default=False, type=bool,
                            help="Boolean toggle to add pinyin with character "
                                 "tones as separate column. Defaults to False.")
        parser.add_argument("-d", "--download",
                            dest="download",
                            default=False, type=bool,
                            help="Should donwload latest cc-cedict or not")
        parser.add_argument("--erhua-keep-space",
                            dest="erhua_keep_space",
                            default=False, type=bool,
                            help="Boolean toggle to keep space before r if "
                                 "--enable-tone-accents is set to true. "
                                 "Defaults to False.")
        self.args = parser.parse_args()

    def download_cedict(self):
        """ Downloads the cedict file and stores it on the filesystem. """
        # if db does not exist or --download is true, download anew
        if not Path("cedict.txt.gz").is_file() or self.args.download:
            with open("cedict.txt.gz", "wb") as file:
                file.write(requests.get(self.WEB_CEDICT_FILE).content)

    def init_db(self):
        """ Drops the cedict database if it already exists, and then creates
            the database. """

        self.conn = sqlite3.connect("database.db")
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS chinese")

        if self.args.enable_tone_accents:
            cursor.execute("CREATE TABLE chinese (rowid INTEGER NOT NULL PRIMARY KEY, traditional TEXT NOT NULL,"
                           "simplified TEXT NOT NULL, pinyin_number TEXT NOT NULL, meanings TEXT NOT NULL, pinyin_tone TEXT NOT NULL)")
        else:
            cursor.execute("CREATE TABLE chinese (rowid INTEGER NOT NULL PRIMARY KEY, traditional TEXT NOT NULL,"
                           "simplified TEXT NOT NULL, pinyin_number TEXT NOT NULL, meanings TEXT NOT NULL)")

        cursor.execute("CREATE UNIQUE INDEX index_chinese_traditional_simplified_pinyin_number "
                       "ON chinese (traditional, simplified, pinyin_number)")

        cursor.execute("CREATE INDEX index_chinese_simplified "
                       "ON chinese (simplified)")

        cursor.execute("CREATE INDEX index_chinese_traditional "
                       "ON chinese (traditional)")
        cursor.close()

    def populate_db(self):
        """ Parses the cedict text file, and populates the cedict database
            with the relevant fields. """

        cursor = self.conn.cursor()

        numberOfEntry = 0

        with gzip.open("cedict.txt.gz", "rt", encoding="utf-8") as file:
            for line in file:
                if line[0] == "#":
                    continue

                trad, simp = line.split(" ")[:2]
                pinyin = line[line.index("[") + 1:line.index("]")]
                english = line[line.index("/") + 1:-2].strip()

                numberOfEntry += 1

                if self.args.enable_tone_accents:
                    pinyin_tone = convert_pinyin(pinyin)
                    if self.args.erhua_keep_space:
                        pinyin_tone = pinyin_tone.replace("r5", "r")
                    else:
                        pinyin_tone = pinyin_tone.replace(" r5", "r")
                    # Some of the pinyin is capitalized so that's why I'm
                    # leaving the preceding l out.
                    pinyin_tone = pinyin_tone.replace("u:1", "ǖ")
                    pinyin_tone = pinyin_tone.replace("u:2", "ǘ")
                    pinyin_tone = pinyin_tone.replace("u:3", "ǚ")
                    pinyin_tone = pinyin_tone.replace("u:4", "ǜ")
                    pinyin_tone = pinyin_tone.replace("u:5", "ü")
                    pinyin_tone = pinyin_tone.replace("u:è", "üè")

                    cursor.execute("INSERT INTO chinese (rowid, traditional,"
                                   "simplified, pinyin_number, meanings,"
                                   "pinyin_tone) VALUES (?,?,?,?,?,?)",
                                   (numberOfEntry, trad, simp, pinyin, english,
                                    pinyin_tone))
                else:
                    cursor.execute("INSERT INTO chinese (rowid, traditional,"
                                   "simplified, pinyin_number, meanings) "
                                   "VALUES (?,?,?,?)",
                                   (numberOfEntry, trad, simp, pinyin, english))

        cursor.close()
        self.conn.commit()


CLI()
