#!/usr/bin/env python3
import sqlite3
import gzip
from pathlib import Path
from argparse import ArgumentParser
import requests
from pinyin import convert_pinyin, attach_er_hua
import re


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
        parser.add_argument("-a", "--enable-tone-accents",
                            dest="enable_tone_accents",
                            default=False, type=bool,
                            help="Boolean toggle to add pinyin with character "
                                 "tones as separate column. Defaults to False.")
        parser.add_argument("-d", "--download",
                            dest="download",
                            default=False, type=bool,
                            help="Should donwload latest cc-cedict or not")
        parser.add_argument("-r", "--erhua-keep-space",
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
        cursor.execute("DROP TABLE IF EXISTS Chinese")

        if self.args.enable_tone_accents:
            cursor.execute(
                "CREATE VIRTUAL TABLE Chinese USING fts4(simplified, traditional, pinyin, meanings, pinyin_tone)")
        else:
            cursor.execute(
                "CREATE VIRTUAL TABLE Chinese USING fts4(simplified, traditional, pinyin, meanings)")

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

                line = line.replace("u:", "ü")

                trad, simp = line.split(" ")[:2]
                pinyin = line[line.index("[") + 1:line.index("]")]
                english = line[line.index(
                    "/") + 1:-2].strip()
                english = re.sub(";\\s+", "/", english)

                numberOfEntry += 1

                removedErHua = "r5" if self.args.erhua_keep_space else " r5"

                if self.args.enable_tone_accents:
                    pinyin_tone = convert_pinyin(pinyin)
                    pinyin_tone = pinyin_tone.replace(removedErHua, "r")

                    # pinyin = attach_er_hua(pinyin)

                    cursor.execute("INSERT INTO Chinese (simplified, traditional, pinyin, meanings, pinyin_tone) VALUES (?,?,?,?,?)",
                                   (simp, trad, pinyin, english, pinyin_tone))
                else:
                    # pinyin = attach_er_hua(pinyin)
                    cursor.execute("INSERT INTO Chinese (simplified, traditional, pinyin, meanings) VALUES (?,?,?,?)",
                                   (simp, trad, pinyin, english))

        cursor.close()
        self.conn.commit()


CLI()
