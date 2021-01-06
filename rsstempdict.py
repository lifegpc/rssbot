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
from time import time
from database import RSSConfig


class rssMetaInfo:
    def __init__(self, messageId: int, chatId: int, meta: dict, itemList: list, hashd: str, config: RSSConfig = None):
        self.messageId = messageId
        self.chatId = chatId
        self.meta = meta
        self.itemList = itemList
        self.hashd = hashd
        self.config = RSSConfig() if config is None else config
        self.__time = time()

    def isTimeOut(self):
        return True if time() - self.__time > 300 else False

    def flushTime(self):
        self.__time = time()


class rssMetaList:
    def __init__(self):
        self.__list = []

    def removeTimeOut(self):
        l = len(self.__list)
        i = 0
        while i < l:
            v = self.__list[i]
            if v.isTimeOut():
                l = l - 1
                self.__list.remove(v)
                continue
            i = i + 1

    def addRSSMeta(self, meta: rssMetaInfo):
        self.removeTimeOut()
        self.__list.append(meta)

    def getRSSMeta(self, hashd: str) -> rssMetaInfo:
        self.removeTimeOut()
        for i in self.__list:
            if hashd == i.hashd:
                return i
        return None
