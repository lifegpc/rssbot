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
from urllib.parse import unquote


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


def removeEmptyLine(s: str) -> str:
    l = s.splitlines(False)
    r = []
    for v in l:
        if v != '':
            r.append(v)
    f = True
    z = ''
    for v in r:
        if f:
            f = False
            z = v
        else:
            z = z + '\n' + v
    return z

def decodeURI(s: str) -> str:
    s = s.replace('%25', '%2525')
    s = s.replace('%3A', '%253A')
    s = s.replace('%3a', '%253A')
    s = s.replace('%2F', '%252F')
    s = s.replace('%2f', '%252F')
    s = s.replace('%3F', '%253F')
    s = s.replace('%3f', '%253F')
    s = s.replace('%23', '%2523')
    s = s.replace('%5B', '%255B')
    s = s.replace('%5b', '%255B')
    s = s.replace('%5D', '%255D')
    s = s.replace('%5d', '%255D')
    s = s.replace('%40', '%2540')
    s = s.replace('%21', '%2521')
    s = s.replace('%24', '%2524')
    s = s.replace('%26', '%2526')
    s = s.replace('%27', '%2527')
    s = s.replace('%28', '%2528')
    s = s.replace('%29', '%2529')
    s = s.replace('%2A', '%252A')
    s = s.replace('%2a', '%252A')
    s = s.replace('%2B', '%252B')
    s = s.replace('%2b', '%252B')
    s = s.replace('%2C', '%252C')
    s = s.replace('%2c', '%252C')
    s = s.replace('%3B', '%253B')
    s = s.replace('%3b', '%253B')
    s = s.replace('%3D', '%253D')
    s = s.replace('%3d', '%253D')
    s = s.replace('%20', '%2520')
    return unquote(s)
