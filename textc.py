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
from time import strftime, localtime, timezone


class textc:
    def __init__(self):
        self.__str = ''

    def tostr(self):
        return self.__str

    def addtotext(self, s: str):
        if self.__str == '':
            self.__str = f"{self.__str}{s}"
        else:
            self.__str = f'{self.__str}\n{s}'


def timeToStr(t: int) -> str:
    te = strftime('%Y-%m-%dT%H:%M:%S', localtime(t))
    op = '-' if timezone > 0 else '+'
    te = te + op + \
        f'{int(abs(timezone)/3600):02}:{int(abs(timezone)%3600/60):02}'
    return te
