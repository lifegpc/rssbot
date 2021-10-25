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
from re import search
from typing import List


class BlackInfo:
    uid: int = None
    op_uid: int = None
    from_config: bool = False
    add_time: int = None
    reason: str = None

    def __init__(self, uid: int, op_uid: int = None, add_time: int = None, reason: str = None):
        self.uid = uid
        self.op_uid = op_uid
        self.from_config = True if self.op_uid is None else False
        self.add_time = add_time
        self.reason = reason


class ConfigBlackList:
    def __init__(self, m, s: str = None):
        from rssbot import main
        self._main: main = m
        self.__list = []
        if s is not None:
            l = s.split(',')
            for i in l:
                if search(r'^[\+-]?[0-9]+$', i) is not None:
                    self.__list.append(int(i))

    def getBlackList(self) -> List[BlackInfo]:
        r = []
        for i in self.__list:
            r.append(BlackInfo(i))
        return r

    def isInBlackList(self, chatId: int) -> bool:
        return chatId in self.__list


class BlackList:
    def __init__(self, m):
        from rssbot import main
        self._main: main = m
        self._configBlackList = ConfigBlackList(m, self._main._setting._blackList)

    def getBlackList(self) -> List[BlackInfo]:
        m = self._configBlackList.getBlackList()
        t = []
        r = []
        for i in m:
            if i.uid not in t:
                t.append(i.uid)
                r.append(i)
        return r

    def isInBlackList(self, chatId: int) -> bool:
        if self._configBlackList.isInBlackList(chatId):
            return True
        return False

    def checkRSSList(self):
        li = self.getBlackList()
        for i in li:
            self._main._db.removeChatInChatList(i.uid)
