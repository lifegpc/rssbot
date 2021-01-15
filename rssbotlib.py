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
from ctypes import Structure, c_bool, c_uint64, c_char_p, CDLL, c_ushort, c_uint16, c_int


class BasicInfo(Structure):
    _fields_ = [("ok", c_bool), ("duration", c_uint64), ("bit_rate", c_uint64), ("has_h264", c_bool), ("has_aac", c_bool), ("mime_type", c_char_p), ("type_long_name", c_char_p),
                ("type_name", c_char_p), ("video_stream_count", c_uint16), ("audio_stream_count", c_uint16), ("subtitle_stream_count", c_uint16), ("width", c_int), ("height", c_int)]


class BasicInfoC:
    def __init__(self, data: BasicInfo):
        self._duration = data.duration if data.duration > 0 else None
        self._bitRate = data.bit_rate if data.bit_rate > 0 else None
        self._hasH264 = data.has_h264
        self._hasAAC = data.has_aac
        self._mimeType = data.mime_type.decode() if data.mime_type is not None else None
        self._typeLongName = data.type_long_name.decode(
        ) if data.type_long_name is not None else None
        self._typeName = data.type_name.decode() if data.type_name is not None else None
        self._videoStreamCount = data.video_stream_count
        self._audioStreamCount = data.audio_stream_count
        self._subtitleStreamCount = data.subtitle_stream_count
        self._width = data.width if data.width > 0 else None
        self._height = data.height if data.height > 0 else None


class RSSBotLib:
    def __init__(self, lib: CDLL):
        self._lib = lib
        self._getBasicInfo = self._lib.getBasicInfo
        self._getBasicInfo.restype = BasicInfo

    def getBasicInfo(self, url: str) -> (bool, BasicInfoC):
        try:
            d: BasicInfo = self._getBasicInfo(url.encode())
            if d.ok:
                return True, BasicInfoC(d)
            return False, None
        except:
            return False, None


def loadRSSBotLib(loc: str):
    if loc is None:
        return None
    try:
        lib = CDLL(loc)
        return RSSBotLib(lib)
    except:
        return None
