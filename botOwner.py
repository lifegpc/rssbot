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


class BotOwnerList:
    def __init__(self, m, s: str = None):
        from rssbot import main
        self._main: main = m
        self.__list = []
        if s is not None:
            l = s.split(',')
            for i in l:
                if search(r'^[\+-]?[0-9]+$', i) is not None:
                    self.__list.append(int(i))

    def getOwnerList(self) -> List[int]:
        r = []
        for i in self.__list:
            r.append(i)
        return r

    def isOwner(self, chatId: int) -> bool:
        return chatId in self.__list
