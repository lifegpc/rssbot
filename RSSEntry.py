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
from json import loads
from config import RSSConfig
from time import time_ns
from typing import List
from hashl import sha256WithBase64


class ChatEntry:
    def __init__(self, data=None, settings=None):
        self._chatId = data[0] if data is not None and data[0] is not None else None
        self._id = data[1] if data is not None and data[1] is not None else None
        try:
            self.config = RSSConfig(
                loads(data[2])) if data is not None and data[2] is not None else RSSConfig()
        except:
            self.config = RSSConfig()
        if settings is not None:
            try:
                self.config.update(settings)
            except Exception:
                pass

    @property
    def chatId(self) -> int:
        if self._chatId is None:
            return None
        if isinstance(self._chatId, int):
            return self._chatId
        else:
            raise ValueError('chatId must be int.')

    @property
    def id(self) -> int:
        return self._id


class HashEntry:
    def __init__(self, data=None, id: int = None, hash: str = None):
        self._id = data[0] if data is not None and data[0] is not None else None
        self._hash = data[1] if data is not None and data[1] is not None else None
        self._time = data[2] if data is not None and data[2] is not None else time_ns()
        if id is not None:
            self._id = id
        if hash is not None:
            self._hash = hash

    @property
    def id(self) -> int:
        return self._id

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def time(self) -> str:
        if self._time is None:
            return None
        if isinstance(self._time, int):
            return self._time
        else:
            raise ValueError('time must be int.')

    @time.setter
    def time(self, v):
        if isinstance(v, int):
            self._time = v


def calHash(id: int, url: dict, item: dict) -> HashEntry:
    hasht = url
    if 'title' in item and item['title'] is not None:
        hasht = hasht + item['title']
    if 'link' in item and item['link'] is not None:
        hasht = hasht + item['link']
    matched = False
    if 'published' in item and item['published'] is not None:
        hasht = hasht + item['published']
        matched = True
    if 'updated' in item and item['updated'] is not None:
        hasht = hasht + item['updated']
        matched = True
    if 'pubDate' in item and item['pubDate'] is not None:
        hasht = hasht + item['pubDate']
        matched = True
    if not matched and 'description' in item and item['description'] is not None:
        hasht = hasht + item['description']
    hashed = sha256WithBase64(hasht)
    return HashEntry(id=id, hash=hashed)


class HashEntries:
    def __init__(self, maxCount: int = 100):
        self.__list = []
        self.__maxCount = maxCount if maxCount is not None and maxCount >= 1 else 100

    def __removeMax(self):
        self.__sort()
        while len(self.__list) > self.__maxCount:
            t = self.__list[0]
            self.__list.remove(t)

    def __sort(self, reverse: bool = False):
        self.__list.sort(key=lambda d: d.time, reverse=reverse)

    def add(self, d: HashEntry):
        if d.hash is not None:
            o = None
            for v in self.__list:
                if v.hash == d.hash:
                    if d.time > v.time:
                        o = v
                        break
                    else:
                        return
            if o is not None:
                self.__list.remove(o)
            self.__list.append(d)
            self.__removeMax()

    def getList(self) -> List[HashEntry]:
        self.__removeMax()
        r = []
        for i in self.__list:
            r.append(i)
        return r

    def has(self, d: HashEntry) -> bool:
        if d.hash is None or d.id is None:
            return False
        for v in self.__list:
            if v.hash == d.hash and v.id == d.id:
                if d.time > v.time:
                    v.time = d.time
                return True
        return False

    def setMaxCount(self, maxCount: int):
        self.__maxCount = maxCount if maxCount >= 1 else 100
        self.__removeMax()


class RSSEntry:
    def __init__(self, data=None, maxCount: int = 100):
        self._title = None
        if data is not None and data[0] is not None:
            self._title = data[0]
        self._url = None
        if data is not None and data[1] is not None:
            self._url = data[1]
        self._interval = None
        if data is not None and data[2] is not None:
            self._interval = data[2]
        self._lastupdatetime = None
        if data is not None and data[3] is not None:
            self._lastupdatetime = data[3]
        self._id = None
        if data is not None and data[4] is not None:
            self._id = data[4]
        self._lasterrortime = None
        if data is not None and data[5] is not None:
            self._lasterrortime = data[5]
        self._forceupdate = False
        if data is not None and data[6] is not None:
            self._forceupdate = bool(data[6])
        self._errorcount = 0
        if data is not None and data[7] is not None:
            self._errorcount = data[7]
        self._settings: dict = {}
        if data is not None and data[8] is not None:
            try:
                self._settings = loads(data[8])
                if not isinstance(self._settings, dict):
                    self._settings = {}
            except Exception:
                self._settings = {}
        self.chatList = []
        self.chatListLoaded = False
        self.hashList = HashEntries(maxCount)
        self.hashListLoaded = False

    @property
    def title(self) -> str:
        return self._title

    @property
    def url(self) -> str:
        return self._url

    @property
    def interval(self) -> int:
        if self._interval is None:
            return None
        if isinstance(self._interval, int):
            return self._interval
        else:
            raise ValueError('interval must be int.')

    @property
    def lastupdatetime(self) -> int:
        if self._lastupdatetime is None:
            return None
        if isinstance(self._lastupdatetime, int):
            return self._lastupdatetime
        else:
            raise ValueError('lastupdatetime must be int.')

    @property
    def id(self) -> int:
        return self._id

    @property
    def lasterrortime(self) -> int:
        if self._lasterrortime is None:
            return None
        if isinstance(self._lasterrortime, int):
            return self._lasterrortime
        else:
            raise ValueError('lasterrortime must be int.')

    @property
    def forceupdate(self) -> bool:
        return self._forceupdate

    @property
    def errorcount(self) -> int:
        if self._errorcount is None:
            return None
        if isinstance(self._errorcount, int):
            return self._errorcount
        else:
            raise ValueError('errorcount must be int.')
