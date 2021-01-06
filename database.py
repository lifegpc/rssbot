# (C) 2021 lifegpc
# This file is part of rssbot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sqlite3
from RSSEntry import RSSEntry
from typing import List
from enum import Enum, unique
from threading import Lock


class RSSConfig:
    def __init__(self):
        self.disable_web_page_preview = False
        self.show_RSS_title = True
        self.show_Content_title = True


@unique
class userStatus(Enum):
    normalStatus = 0
    needInputChatId = 1


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
config TEXT,
id TEXT,
PRIMARY KEY (id)
);''')
        if 'userList' not in self._exist_tables:
            self._db.execute('''CREATE TABLE userList (
userId INT,
id TEXT
)''')
        if 'userStatus' not in self._exist_tables:
            self._db.execute('''CREATE TABLE userStatus (
userId INT,
status INT,
hashd TEXT,
PRIMARY KEY (userId)
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
        self._value_lock = Lock()
        self._db = sqlite3.connect('data.db', check_same_thread=False)
        ok = self.__check_database()
        if not ok:
            self.__create_table()

    def __write_version(self):
        self._db.execute(
            f'INSERT INTO config VALUES ({self._version[0]}, {self._version[1]}, {self._version[2]}, {self._version[3]});')
        self._db.commit()

    def getAllRSSList(self) -> List[RSSEntry]:
        with self._value_lock:
            cur = self._db.execute(f'SELECT * FROM RSSList;')
            r = []
            for i in cur:
                r.append(RSSEntry(i))
            return r

    def getUserStatus(self, userId: int) -> (userStatus, str):
        with self._value_lock:
            cur = self._db.execute(
                f'SELECT * FROM userStatus WHERE userId={userId}')
            for i in cur:
                try:
                    return userStatus(i[1]), i[2]
                except:
                    pass
            return userStatus.normalStatus, ''

    def setUserStatus(self, userId: int, status: userStatus = userStatus.normalStatus, hashd: str = '') -> bool:
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f'SELECT * FROM userStatus WHERE userId={userId}')
            except:
                return False
            have_data = False
            now = None
            for i in cur:
                have_data = True
                try:
                    now = (userStatus(i[1]), i[2])
                except:
                    pass
            if have_data and now is not None and now[0] == status and now[1] == hashd:
                return True
            try:
                if have_data:
                    cur = self._db.execute(
                        f'UPDATE userStatus SET status={status.value}, hashd="{hashd}" WHERE userId={userId}')
                else:
                    cur = self._db.execute(
                        f'INSERT INTO userStatus VALUES ({userId}, {status.value}, "{hashd}");')
                self._db.commit()
                return True
            except:
                return False
