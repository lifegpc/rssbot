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
from enum import unique, Enum
from traceback import print_exc
try:
    from _rssbotlib import version, VideoInfo
    have_rssbotlib = True
except ImportError:
    have_rssbotlib = False


@unique
class AddVideoInfoResult(Enum):
    OK = 0
    ERROR = 1
    IsHLS = 2


if have_rssbotlib:
    class RSSBotLib:
        def __init__(self, m):
            from rssbot import main
            self._main: main = m
            self._version = version()
            if self._version is None or self._version != [1, 0, 0, 0]:
                raise ValueError('RSSBotLib Version unknown or not supported.')

        def addVideoInfo(self, url: str, data: dict, loc: str = None) -> AddVideoInfoResult:
            try:
                v = VideoInfo()
                if loc is not None:
                    if not v.parse(loc):
                        if not v.parse(url):
                            return AddVideoInfoResult.ERROR
                else:
                    if not v.parse(url):
                        return AddVideoInfoResult.ERROR
                tn = v.type_name
                if tn is not None and tn == 'hls':
                    return AddVideoInfoResult.IsHLS
                d = v.duration
                if d is not None:
                    data['duration'] = max(round(d), 1)
                sl = v.streams
                for i in sl:
                    if i.is_video:
                        w = i.width
                        if w is not None and w > 0:
                            data['width'] = w
                            break
                for i in sl:
                    if i.is_video:
                        h = i.height
                        if h is not None and h > 0:
                            data['height'] = h
                            break
                return AddVideoInfoResult.OK
            except Exception:
                print_exc()
                return AddVideoInfoResult.ERROR


def loadRSSBotLib(m):
    if have_rssbotlib:
        return RSSBotLib(m)
    else:
        return None
