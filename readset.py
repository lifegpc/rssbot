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
class settings:
    def __init__(self, fn: str=None):
        if fn is not None:
            self.parse(fn)
    
    def parse(self, fn: str):
        d = {}
        with open(fn, 'r', encoding='utf8') as f:
            t = f.read()
            for i in t.splitlines(False):
                l = i.split('=', 2)
                if len(l) == 2:
                    d[l[0]] = l[1]
        self._token = d['token'] if 'token' in d else None
        self._maxCount = int(d['maxCount']) if 'maxCount' in d and d['maxCount'].isnumeric() else 100
