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
class RetryTTLList:
    def __init__(self, s: str = None):
        self.__list = []
        if s is not None:
            l = s.split(',')
            for i in l:
                if i.isnumeric():
                    self.__list.append(int(i))
        if len(self.__list) == 0:
            self.__list.append(30)

    def __getitem__(self, index: int) -> int:
        index = int(index)
        return None if index <= 0 else self.__list[index-1] if index <= len(self.__list) else self.__list[-1]
