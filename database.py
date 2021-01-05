import sqlite3


class database:
    def __check_database(self):
        cur = self._db.execute('SELECT * FROM main.sqlite_master;')
        self._exist_tables = {}
        for i in cur:
            if i[0] == 'table':
                self._exist_tables[i[1]] = i
        for i in ['config', 'RSSList']:
            if i not in self._exist_tables:
                return False
        return True

    def __create_table(self):
        if 'config' not in self._exist_tables:
            self._db.execute(f'''CREATE TABLE config (
version1 INT,
version2 INT,
version3 INT,
version4 INT
);''')
            self.__write_version()
        if 'RSSList' not in self._exist_tables:
            self._db.execute(f'''CREATE TABLE RSSList (
title TEXT,
url TEXT,
interval INT,
lastupdatetime INT,
type INT,
id TEXT,
PRIMARY KEY (url)
);''')
        if 'userList' not in self._exist_tables:
            self._db.execute('''CREATE TABLE userList (
userId INT,
id TEXT
)''')
        if 'channelList' not in self._exist_tables:
            self._db.execute('''CREATE TABLE channelList (
channelId INT,
id TEXT
)''')
        if 'hashList' not in self._exist_tables:
            self._db.execute('''CREATE TABLE hashList (
id TEXT,
hash TEXT,
PRIMARY KEY (hash)
)''')
        self._db.commit()

    def __init__(self):
        self._version = [1, 0, 0, 0]
        self._db = sqlite3.connect('data.db')
        ok = self.__check_database()
        if not ok:
            self.__create_table()

    def __write_version(self):
        self._db.execute(
            f'INSERT INTO config VALUES ({self._version[0]}, {self._version[1]}, {self._version[2]}, {self._version[3]});')
        self._db.commit()
