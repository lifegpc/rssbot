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
from config import RSSConfig
from RSSEntry import RSSEntry, ChatEntry, HashEntry, HashEntries
from typing import List
from enum import Enum, unique
from threading import Lock
from hashl import sha256WithBase64
from time import time


def dealtext(s: str):
    return s.replace("'", "''")


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
        for i in ['config', 'RSSList', 'chatList', 'userStatus', 'hashList']:
            if i not in self._exist_tables:
                return False
        v = self.__read_version()
        if v is None:
            return False
        if v < self._version:
            if v == [1, 0, 0, 0]:
                self._db.execute('ALTER TABLE RSSList ADD lasterrortime INT;')
                self._db.commit()
            self.__write_version()
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
id TEXT,
lasterrortime INT,
PRIMARY KEY (id)
);''')
        if 'chatList' not in self._exist_tables:
            self._db.execute('''CREATE TABLE chatList (
chatId INT,
id TEXT,
config TEXT
)''')
        if 'userStatus' not in self._exist_tables:
            self._db.execute('''CREATE TABLE userStatus (
userId INT,
status INT,
hashd TEXT,
PRIMARY KEY (userId)
)''')
        if 'hashList' not in self._exist_tables:
            self._db.execute('''CREATE TABLE hashList (
id TEXT,
hash TEXT,
time INT,
PRIMARY KEY (hash)
)''')
        self._db.commit()

    def __init__(self, m, loc: str):
        self._version = [1, 0, 0, 1]
        self._value_lock = Lock()
        self._db = sqlite3.connect(loc, check_same_thread=False)
        ok = self.__check_database()
        if not ok:
            self.__create_table()
        from rssbot import main
        self._main: main = m

    def __removeRSSEntry(self, id: str) -> bool:
        try:
            self._db.execute(f'DELETE FROM RSSList WHERE id="{id}"')
            self._db.execute(f'DELETE FROM hashList WHERE id="{id}"')
            self._db.commit()
            return True
        except:
            return False

    def __write_version(self):
        self._db.execute('DELETE FROM config;')
        self._db.execute(
            f'INSERT INTO config VALUES ({self._version[0]}, {self._version[1]}, {self._version[2]}, {self._version[3]});')
        self._db.commit()

    def __read_version(self) -> List[int]:
        cur = self._db.execute(f'SELECT * FROM config;')
        for i in cur:
            return [k for k in i]

    def addRSSList(self, title: str, url: str, chatId: int, config: RSSConfig, ttl: int = None, hashEntries: HashEntries = None):
        with self._value_lock:
            try:
                hashd = sha256WithBase64(url)
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE id="{hashd}"')
                has_data = False
                for i in cur:  # pylint: disable=unused-variable
                    has_data = True
                    break
                if has_data:
                    self._db.execute(
                        f"UPDATE RSSList SET title='{dealtext(title)}', interval={ttl if ttl is not None else 'null'} WHERE id='{hashd}'")
                else:
                    self._db.execute(
                        f"INSERT INTO RSSList VALUES ('{dealtext(title)}', '{dealtext(url)}', {ttl if ttl is not None else 'null'}, {int(time())}, '{hashd}', null)")
                cur = self._db.execute(
                    f'SELECT * FROM chatList WHERE id="{hashd}" AND chatId={chatId}')
                has_data2 = False
                for i in cur:
                    has_data2 = True
                    break
                if has_data2:
                    self._db.execute(
                        f'DELETE FROM chatList WHERE id="{hashd}" AND chatId={chatId}')
                self._db.execute(
                    f"INSERT INTO chatList VALUES ({chatId}, '{hashd}', '{dealtext(config.toJson())}')")
                if hashEntries is not None and not has_data:
                    cur = self._db.execute(
                        f"SELECT * FROM hashList WHERE id='{hashd}'")
                    has_data3 = False
                    for i in cur:
                        has_data3 = True
                        break
                    if has_data3:
                        self._db.execute(
                            f"DELETE FROM hashList WHERE id='{hashd}'")
                    for v in hashEntries.getList():
                        self._db.execute(
                            f"INSERT INTO hashList VALUES ('{v.id}', '{v.hash}', {v.time})")
                self._db.commit()
                return True
            except:
                return False

    def getAllRSSList(self) -> List[RSSEntry]:
        with self._value_lock:
            cur = self._db.execute(f'SELECT * FROM RSSList;')
            r = []
            for i in cur:
                temp = RSSEntry(i, self._main._setting._maxCount)
                cur2 = self._db.execute(
                    f'SELECT * FROM chatList WHERE id="{temp.id}"')
                for i2 in cur2:
                    temp2 = ChatEntry(i2)
                    temp.chatList.append(temp2)
                cur3 = self._db.execute(
                    f"SELECT * FROM hashList WHERE id='{temp.id}' ORDER BY time")
                for i3 in cur3:
                    temp.hashList.add(HashEntry(i3))
                if len(temp.chatList) == 0:
                    self.__removeRSSEntry(temp.id)
                else:
                    r.append(temp)
            return r

    def getRSSListByChatId(self, chatId: int) -> List[RSSEntry]:
        with self._value_lock:
            cur = self._db.execute(
                f"SELECT RSSList.title, RSSList.url, RSSList.interval, RSSList.lastupdatetime, RSSList.id, RSSList.lasterrortime, chatList.config FROM RSSList, chatList WHERE chatList.chatId = {chatId} AND RSSList.id = chatList.id ORDER BY title")
            RSSEntries = []
            for i in cur:
                rssEntry = RSSEntry(i, self._main._setting._maxCount)
                rssEntry.chatList.append(ChatEntry((chatId, i[4], i[6])))
                RSSEntries.append(rssEntry)
            return RSSEntries

    def getUserStatus(self, userId: int) -> (userStatus, str):
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f'SELECT * FROM userStatus WHERE userId={userId}')
                for i in cur:
                    return userStatus(i[1]), i[2]
            except:
                pass
            return userStatus.normalStatus, ''

    def removeItemInChatList(self, chatId: int, id: str):
        with self._value_lock:
            try:
                self._db.execute(
                    f"DELETE FROM chatList WHERE chatId={chatId} AND id='{id}'")
                self._db.commit()
                return True
            except:
                return False

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

    def updateChatConfig(self, chatEntry: ChatEntry) -> bool:
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f"SELECT * FROM chatList WHERE chatId={chatEntry.chatId} AND id='{chatEntry.id}'")
                has_data = False
                for i in cur:  # pylint: disable=unused-variable
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute(
                    f"UPDATE chatList SET config='{dealtext(chatEntry.config.toJson())}' WHERE chatId={chatEntry.chatId} AND id='{chatEntry.id}'")
                self._db.commit()
                return True
            except:
                return False

    def updateRSS(self, title: str, url: str, lastupdatetime: int, hashEntries: HashEntries, ttl: int = None):
        with self._value_lock:
            try:
                hashd = sha256WithBase64(url)
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE id="{hashd}"')
                has_data = False
                for i in cur:  # pylint: disable=unused-variable
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute(
                    f"UPDATE RSSList SET title='{dealtext(title)}', interval={ttl if ttl is not None else 'null'}, lastupdatetime={lastupdatetime} WHERE id='{hashd}'")
                cur = self._db.execute(
                    f"SELECT * FROM hashList WHERE id='{hashd}'")
                has_data2 = False
                for i in cur:
                    has_data2 = True
                    break
                if has_data2:
                    self._db.execute(
                        f"DELETE FROM hashList WHERE id='{hashd}'")
                for v in hashEntries.getList():
                    self._db.execute(
                        f"INSERT INTO hashList VALUES ('{v.id}', '{v.hash}', {v.time})")
                self._db.commit()
            except:
                return False

    def updateRSSWithError(self, url: str, lasterrortime: int):
        with self._value_lock:
            try:
                hashd = sha256WithBase64(url)
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE id="{hashd}"')
                has_data = False
                for i in cur:  # pylint: disable=unused-variable
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute(
                    f"UPDATE RSSList SET lasterrortime={lasterrortime} WHERE id='{hashd}'")
                self._db.commit()
            except:
                return False
