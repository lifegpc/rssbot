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
from typing import List, Optional, Tuple
from enum import Enum, unique
from threading import Lock
from time import time
from blackList import BlackInfo, BlackInfoList


VERSION_TABLE = '''CREATE TABLE version (
id TEXT,
v1 INT,
v2 INT,
v3 INT,
v4 INT,
PRIMARY KEY (id)
);'''
RSSLIST_TABLE = '''CREATE TABLE RSSList (
title TEXT,
url TEXT,
interval INT,
lastupdatetime INT,
id INTEGER,
lasterrortime INT,
forceupdate BOOLEAN,
errorcount INT,
settings TEXT,
PRIMARY KEY (id)
);'''
CHATLIST_TABLE = '''CREATE TABLE chatList (
chatId INT,
id INT,
config TEXT
)'''
HASHLIST_TABLE = '''CREATE TABLE hashList (
id INT,
hash TEXT,
time INT,
PRIMARY KEY (hash)
)'''
USERSTATUS_TABLE = '''CREATE TABLE userStatus (
userId INT,
status INT,
hashd TEXT,
PRIMARY KEY (userId)
)'''
USERBLACKLIST_TABLE = '''CREATE TABLE userBlackList (
userId INT,
op_uid INT,
add_time INT,
reason TEXT,
name TEXT,
PRIMARY KEY (userId)
)'''
CHATNAMECACHE_TABLE = '''CREATE TABLE chatNameCache (
id INT,
name TEXT,
time INT,
PRIMARY KEY (id)
)'''


@unique
class userStatus(Enum):
    normalStatus = 0
    needInputChatId = 1


class database:
    def __check_database(self):
        self.__updateExistsTable()
        v = self.__read_version()
        if v is None:
            return False
        if v < self._version:
            if v == [1, 0, 0, 0]:
                self._db.execute('ALTER TABLE RSSList ADD lasterrortime INT;')
                self._db.commit()
            if v < [1, 0, 0, 2]:
                self._db.execute(
                    'ALTER TABLE RSSList ADD forceupdate BOOLEAN;')
                self._db.execute('UPDATE RSSList SET forceupdate=false;')
                self._db.commit()
            if v < [1, 0, 0, 3]:
                self._db.execute('ALTER TABLE RSSList ADD errorcount INT;')
                self._db.execute('UPDATE RSSList SET errorcount=0;')
                self._db.commit()
            if v < [1, 0, 0, 4]:
                self._db.execute('DROP TABLE config;')
                self._db.execute(VERSION_TABLE)
                self._db.commit()
            if v < [1, 0, 0, 5]:
                cur = self._db.execute('SELECT * FROM RSSList;')
                self._db.execute('ALTER TABLE RSSList RENAME TO RSSList_old;')
                k = 0
                m = {}
                self._db.execute(RSSLIST_TABLE)
                for i in cur:
                    m[i[4]] = k
                    l = list(i)
                    l[4] = k
                    self._db.execute(
                        'INSERT INTO RSSList VALUES (?, ?, ?, ?, ?, ?, ?, ?);',
                        tuple(l))
                    k += 1
                self._db.execute('DROP TABLE RSSList_old;')
                cur = self._db.execute('SELECT * FROM chatList;')
                self._db.execute('ALTER TABLE chatList RENAME TO chatList_old;')
                self._db.execute(CHATLIST_TABLE)
                for i in cur:
                    l = list(i)
                    l[1] = m[i[1]]
                    self._db.execute(
                        'INSERT INTO chatList VALUES (?, ?, ?);', tuple(l))
                self._db.execute('DROP TABLE chatList_old;')
                cur = self._db.execute('SELECT * FROM hashList;')
                self._db.execute('ALTER TABLE hashList RENAME TO hashList_old;')
                self._db.execute(HASHLIST_TABLE)
                for i in cur:
                    l = list(i)
                    l[0] = m[i[0]]
                    self._db.execute(
                        'INSERT INTO hashList VALUES (?, ?, ?);', tuple(l))
                self._db.execute('DROP TABLE hashList_old;')
                self._db.commit()
            if v < [1, 0, 0, 6]:
                self._db.execute(USERBLACKLIST_TABLE)
                self._db.commit()
            if v < [1, 0, 0, 7]:
                self._db.execute('ALTER TABLE userBlackList ADD name TEXT;')
                self._db.commit()
            if v < [1, 0, 0, 8]:
                self._db.execute('ALTER TABLE RSSList ADD settings TEXT;')
                self._db.commit()
            if v < [1, 0, 0, 9]:
                self._db.execute(CHATNAMECACHE_TABLE)
                self._db.commit()
            self._db.execute('VACUUM;')
            self.__updateExistsTable()
            self.__write_version()
        return True

    def __create_table(self):
        if 'version' not in self._exist_tables:
            self._db.execute(VERSION_TABLE)
            self.__write_version()
        if 'RSSList' not in self._exist_tables:
            self._db.execute(RSSLIST_TABLE)
        if 'chatList' not in self._exist_tables:
            self._db.execute(CHATLIST_TABLE)
        if 'userStatus' not in self._exist_tables:
            self._db.execute(USERSTATUS_TABLE)
        if 'hashList' not in self._exist_tables:
            self._db.execute(HASHLIST_TABLE)
        if 'userBlackList' not in self._exist_tables:
            self._db.execute(USERBLACKLIST_TABLE)
        if 'chatNameCache' not in self._exist_tables:
            self._db.execute(CHATNAMECACHE_TABLE)
        self._db.commit()

    def __init__(self, m, loc: str):
        self._version = [1, 0, 0, 9]
        self._value_lock = Lock()
        self._db = sqlite3.connect(loc, check_same_thread=False)
        self._db.execute('VACUUM;')
        self._db.commit()
        ok = self.__check_database()
        if not ok:
            self.__create_table()
        from rssbot import main
        self._main: main = m

    def __isNewVersionType(self):
        if 'version' in self._exist_tables:
            return True
        else:
            return False

    def __removeRSSEntry(self, id: int) -> bool:
        try:
            self._db.execute(f'DELETE FROM RSSList WHERE id=?;', (id,))
            self._db.execute(f'DELETE FROM hashList WHERE id=?;', (id,))
            self._db.commit()
            return True
        except:
            return False

    def __write_version(self):
        if self.__read_version() is None:
            self._db.execute('INSERT INTO version VALUES (?, ?, ?, ?, ?);',
                             tuple(['main'] + self._version))
        else:
            self._db.execute(
                "UPDATE version SET v1=?, v2=?, v3=?, v4=? WHERE id='main';",
                tuple(self._version))
        self._db.commit()

    def __read_version(self) -> List[int]:
        if 'version' not in self._exist_tables:
            return None
        if self.__isNewVersionType():
            cur = self._db.execute("SELECT * FROM version WHERE id='main';")
            for i in cur:
                return [k for k in i if isinstance(k, int)]
        else:
            cur = self._db.execute(f'SELECT * FROM config;')
            for i in cur:
                return [k for k in i]

    def __updateExistsTable(self):
        cur = self._db.execute('SELECT * FROM main.sqlite_master;')
        self._exist_tables = {}
        for i in cur:
            if i[0] == 'table':
                self._exist_tables[i[1]] = i

    def addRSSList(self, title: str, url: str, chatId: int, config: RSSConfig, ttl: int = None, hashEntries: HashEntries = None):
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE url=?;', (url,))
                has_data = False
                for i in cur:
                    has_data = True
                    hashd = i[4]
                if has_data:
                    self._db.execute(
                        f"UPDATE RSSList SET title=?, interval=?, settings=? WHERE id=?;",
                        (title, ttl, config.toGlobalJson(), hashd))
                else:
                    self._db.execute(
                        f"INSERT INTO RSSList (title, url, interval, lastupdatetime, lasterrortime, forceupdate, errorcount, settings) VALUES (?, ?, ?, ?, null, false, 0, ?);",
                        (title, url, ttl, int(time()), config.toGlobalJson()))
                    cur = self._db.execute(
                        'SELECT * FROM RSSList WHERE url=?;', (url,))
                    for i in cur:
                        hashd = i[4]
                        break
                cur = self._db.execute(
                    f'SELECT * FROM chatList WHERE id=? AND chatId=?;',
                    (hashd, chatId))
                has_data2 = False
                for i in cur:
                    has_data2 = True
                    break
                if has_data2:
                    self._db.execute(
                        f'DELETE FROM chatList WHERE id=? AND chatId=?;',
                        (hashd, chatId))
                self._db.execute(
                    f"INSERT INTO chatList VALUES (?, ?, ?);",
                    (chatId, hashd, config.toJson()))
                if hashEntries is not None and not has_data:
                    cur = self._db.execute(
                        f"SELECT * FROM hashList WHERE id=?;", (hashd,))
                    has_data3 = False
                    for i in cur:
                        has_data3 = True
                        break
                    if has_data3:
                        self._db.execute(
                            f"DELETE FROM hashList WHERE id=?;", (hashd,))
                    for v in hashEntries.getList():
                        self._db.execute(
                            f"INSERT INTO hashList VALUES (?, ?, ?);",
                            (hashd, v.hash, v.time))
                self._db.commit()
                return True
            except:
                return False

    def addBlackInfo(self, i: BlackInfo) -> bool:
        with self._value_lock:
            try:
                have_value = False
                cur = self._db.execute('SELECT * FROM userBlackList WHERE userId=?;', (i.uid,))
                for i in cur:
                    have_value = True
                    break
                if have_value:
                    self._db.execute('UPDATE userBlackList SET op_uid=?, add_time=?, reason=?, name=? WHERE userId=?;', (i.op_uid, i.add_time, i.reason, i.title, i.uid))
                else:
                    self._db.execute('INSERT INTO userBlackList VALUES (?, ?, ?, ?, ?);', (i.uid, i.op_uid, i.add_time, i.reason, i.title))
                self._db.commit()
                return True
            except Exception:
                return False

    def getAllRSSList(self) -> List[RSSEntry]:
        with self._value_lock:
            cur = self._db.execute(f'SELECT * FROM RSSList;')
            r = []
            for i in cur:
                temp = RSSEntry(i, self._main._setting.maxCount)
                cur2 = self._db.execute(
                    f'SELECT * FROM chatList WHERE id=?;', (temp.id,))
                for i2 in cur2:
                    temp2 = ChatEntry(i2, temp._settings)
                    temp.chatList.append(temp2)
                cur3 = self._db.execute(
                    f"SELECT * FROM hashList WHERE id=? ORDER BY time;", (temp.id,))
                for i3 in cur3:
                    temp.hashList.add(HashEntry(i3))
                if len(temp.chatList) == 0:
                    self.__removeRSSEntry(temp.id)
                else:
                    r.append(temp)
            return r

    def getBlackList(self) -> BlackInfoList:
        with self._value_lock:
            cur = self._db.execute('SELECT * FROM userBlackList;')
            li = BlackInfoList()
            for i in cur:
                li.append(BlackInfo(i[0], i[1], i[2], i[3], i[4]))
            return li

    def getChatCount(self) -> int:
        with self._value_lock:
            cur = self._db.execute('SELECT COUNT(DISTINCT chatId) FROM chatList;')
            for i in cur:
                return i[0]
            return None

    def getChatIdList(self) -> int:
        with self._value_lock:
            cur = self._db.execute('SELECT DISTINCT chatId FROM chatList;')
            r = []
            for i in cur:
                r.append(i[0])
            return r

    def getChatName(self, chat_id: int, maxCacheTime: int = 3600) -> Optional[str]:
        with self._value_lock:
            cur = self._db.execute('SELECT name FROM chatNameCache WHERE id = ? AND time > ?;', (chat_id, round(time()) - maxCacheTime))
            for i in cur:
                return i[0]
            return None

    def getChatRSSCount(self) -> int:
        with self._value_lock:
            cur = self._db.execute('SELECT COUNT(*) FROM chatList;')
            for i in cur:
                return i[0]
            return None

    def getHashCount(self) -> int:
        with self._value_lock:
            cur = self._db.execute('SELECT COUNT(*) FROM hashList;')
            for i in cur:
                return i[0]
            return None

    def getRSSList(self) -> Optional[List[RSSEntry]]:
        '''返回不带chatList和hashList的RSS列表'''
        with self._value_lock:
            cur = self._db.execute(f'SELECT * FROM RSSList;')
            r = []
            for i in cur:
                r.append(RSSEntry(i, self._main._setting.maxCount))
            return r

    def getRSSByIdAndChatId(self, id: int, chatId: int) -> RSSEntry:
        while self._value_lock:
            cur = self._db.execute('SELECT RSSList.title, RSSList.url, RSSList.interval, RSSList.lastupdatetime, RSSList.id, RSSList.lasterrortime, RSSList.forceupdate, RSSList.errorcount, RSSList.settings, chatList.config FROM chatList INNER JOIN RSSList ON RSSList.id = chatList.id WHERE chatList.chatId = ? AND chatlist.id = ?;', (chatId, id))
            for i in cur:
                rss = RSSEntry(i, self._main._setting.maxCount)
                rss.chatList.append(ChatEntry((chatId, i[4], i[9]), rss._settings))
                return rss
            return None

    def getRSSCount(self) -> int:
        with self._value_lock:
            cur = self._db.execute('SELECT COUNT(*) FROM RSSList;')
            for i in cur:
                return i[0]
            return None

    def getRSSListByChatId(self, chatId: int) -> List[RSSEntry]:
        with self._value_lock:
            cur = self._db.execute(
                f"SELECT RSSList.title, RSSList.url, RSSList.interval, RSSList.lastupdatetime, RSSList.id, RSSList.lasterrortime, RSSList.forceupdate, RSSList.errorcount, RSSList.settings, chatList.config FROM RSSList, chatList WHERE chatList.chatId = ? AND RSSList.id = chatList.id ORDER BY title;", (chatId,))
            RSSEntries = []
            for i in cur:
                rssEntry = RSSEntry(i, self._main._setting.maxCount)
                rssEntry.chatList.append(ChatEntry((chatId, i[4], i[9]), rssEntry._settings))
                RSSEntries.append(rssEntry)
            return RSSEntries

    def getRSSSettingsByUrl(self, url: str) -> Optional[str]:
        with self._value_lock:
            try:
                cur = self._db.execute('SELECT settings FROM RSSList WHERE url=?;', (url,))
                for i in cur:
                    return i[0]
            except Exception:
                return None

    def getUserBlackListCount(self) -> int:
        with self._value_lock:
            cur = self._db.execute('SELECT COUNT(*) FROM userBlackList;')
            for i in cur:
                return i[0]
            return None

    def getUserStatus(self, userId: int) -> Tuple[userStatus, str]:
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f'SELECT * FROM userStatus WHERE userId=?;', (userId,))
                for i in cur:
                    return userStatus(i[1]), i[2]
            except:
                pass
            return userStatus.normalStatus, ''

    def removeChatInChatList(self, chatId: int):
        with self._value_lock:
            try:
                self._db.execute("DELETE FROM chatList WHERE chatId=?;", (chatId,))
                self._db.commit()
                return True
            except:
                return False

    def removeFromBlackList(self, userId: int):
        with self._value_lock:
            try:
                self._db.execute('DELETE FROM userBlackList WHERE userId=?;', (userId,))
                self._db.commit()
                return True
            except Exception:
                return False

    def removeItemInChatList(self, chatId: int, id: int):
        with self._value_lock:
            try:
                self._db.execute(
                    f"DELETE FROM chatList WHERE chatId=? AND id=?;",
                    (chatId, id))
                self._db.commit()
                return True
            except:
                return False

    def saveChatName(self, chatId: int, name: str) -> bool:
        with self._value_lock:
            try:
                self._db.execute('INSERT OR REPLACE INTO chatNameCache VALUES (?, ?, ?);', (chatId, name, round(time())))
                self._db.commit()
                return True
            except:
                return False

    def setRSSForceUpdate(self, id: int, forceupdate: bool) -> bool:
        with self._value_lock:
            try:
                hashd = id
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE id=?;', (hashd,))
                has_data = False
                for i in cur:  # pylint: disable=unused-variable
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute(
                    f"UPDATE RSSList SET forceupdate=? WHERE id=?;",
                    (forceupdate, hashd))
                self._db.commit()
                return True
            except:
                return False

    def setUserStatus(self, userId: int, status: userStatus = userStatus.normalStatus, hashd: str = '') -> bool:
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f'SELECT * FROM userStatus WHERE userId=?;', (userId,))
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
                        f'UPDATE userStatus SET status=?, hashd=? WHERE userId=?;',
                        (status.value, hashd, userId))
                else:
                    cur = self._db.execute(
                        f'INSERT INTO userStatus VALUES (?, ?, ?);',
                        (userId, status.value, hashd))
                self._db.commit()
                return True
            except:
                return False

    def updateChatConfig(self, chatEntry: ChatEntry) -> bool:
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f"SELECT * FROM chatList WHERE chatId=? AND id=?;",
                    (chatEntry.chatId, chatEntry.id))
                has_data = False
                for i in cur:  # pylint: disable=unused-variable
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute(
                    f"UPDATE chatList SET config=? WHERE chatId=? AND id=?;",
                    (chatEntry.config.toJson(), chatEntry.chatId, chatEntry.id))
                self._db.commit()
                return True
            except:
                return False

    def updateRSS(self, title: str, id: int, lastupdatetime: int, hashEntries: HashEntries, ttl: int = None):
        with self._value_lock:
            try:
                hashd = id
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE id=?;', (hashd,))
                has_data = False
                for i in cur:  # pylint: disable=unused-variable
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute(
                    f"UPDATE RSSList SET title=?, interval=?, lastupdatetime=?, errorcount=0 WHERE id=?;",
                    (title, ttl, lastupdatetime, hashd))
                cur = self._db.execute(
                    f"SELECT * FROM hashList WHERE id=?;", (hashd,))
                has_data2 = False
                for i in cur:
                    has_data2 = True
                    break
                if has_data2:
                    self._db.execute(
                        f"DELETE FROM hashList WHERE id=?;", (hashd,))
                for v in hashEntries.getList():
                    self._db.execute(
                        f"INSERT INTO hashList VALUES (?, ?, ?);",
                        (v.id, v.hash, v.time))
                self._db.commit()
                return True
            except:
                return False

    def updateRSSSettings(self, id: int, settings: RSSConfig):
        with self._value_lock:
            try:
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE id=?;', (id,))
                has_data = False
                for i in cur:
                    rss = RSSEntry(i, self._main._setting.maxCount)
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute('UPDATE RSSList SET settings=? WHERE id=?;', (settings.toGlobalJson(), id))
                self._db.commit()
                return True
            except Exception:
                return False

    def updateRSSWithError(self, id: int, lasterrortime: int):
        with self._value_lock:
            try:
                hashd = id
                cur = self._db.execute(
                    f'SELECT * FROM RSSList WHERE id=?;', (hashd,))
                has_data = False
                for i in cur:
                    rss = RSSEntry(i, self._main._setting.maxCount)
                    has_data = True
                    break
                if not has_data:
                    return False
                self._db.execute(
                    f"UPDATE RSSList SET lasterrortime=?, errorcount=? WHERE id=?;", (lasterrortime, rss.errorcount + 1, hashd))
                self._db.commit()
                return True
            except:
                return False
