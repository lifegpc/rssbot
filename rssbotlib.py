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
from ctypes import Structure, c_bool, c_int64, c_char_p, CDLL, c_ushort, c_uint16, c_int, POINTER, c_size_t
from enum import Enum, unique


@unique
class AddVideoInfoResult(Enum):
    OK = 0
    ERROR = 1
    IsHLS = 2


@unique
class MediaType(Enum):
    UNKNOWN = 0
    VIDEO = 1
    AUDIO = 2
    SUBTITLE = 3


@unique
class StreamType(Enum):
    NONE = 0
    UNKNOWN = 1
    MPEG1VIDEO = 2
    MPEG2VIDEO = 3
    H261 = 4
    H263 = 5
    RV = 6
    MPEG4 = 7
    RAWVIDEO = 8
    MSMPEG4 = 9
    WMV = 10
    FLV = 11
    H264 = 12
    VP7 = 13
    VP8 = 14
    VP9 = 15
    HEVC = 16
    VVC = 17
    PCM = 18
    ADPCM = 19
    MP3 = 20
    AAC = 21
    AC3 = 22
    DTS = 23
    WMA = 24
    FLAC = 25
    APE = 26
    EAC3 = 27
    OPUS = 28
    DVD_SUBTITLE = 29
    TEXT = 30
    ASS = 31
    MOV_TEXT = 32
    HDMV_PGS_SUBTITLE = 33
    SRT = 34
    MICRODVD = 35
    WEBVTT = 36
    HDMV_TEXT_SUBTITLE = 37
    TTML = 38


class StreamInfo(Structure):
    _fields_ = [("originMediaType", c_int), ("mediaType", c_int), ("originCodecID", c_int), ("codecID", c_int), ("bitRate", c_int64), ("bitsPerCodedSample", c_int),
                ("bitsPerRawSample", c_int), ("profile", c_int), ("level", c_int), ("width", c_int), ("height", c_int), ("channels", c_int), ("sampleRate", c_int)]


class StreamInfoC:
    def __init__(self, data: StreamInfo, lib):
        self._lib: RSSBotLib = lib
        self._originMediaType = data.originMediaType
        try:
            self._mediaType = MediaType(data.mediaType)
        except:
            self._mediaType = MediaType.UNKNOWN
        self._originCodecID = data.originCodecID
        try:
            self._codecID = StreamType(data.codecID)
        except:
            self._codecID = StreamType.UNKNOWN
        self._bitRate = data.bitRate if data.bitRate > 0 else None
        self._bitsPerCodedSample = data.bitsPerCodedSample if data.bitsPerCodedSample > 0 else None
        self._bitsPerRawSample = data.bitsPerRawSample if data.bitsPerRawSample > 0 else None
        self._profile = data.profile
        self._level = data.level
        self._width = data.width if data.width > 0 else None
        self._height = data.height if data.height > 0 else None
        self._channels = data.channels if data.channels > 0 else None
        self._sampleRate = data.sampleRate if data.sampleRate > 0 else None

    def isVideo(self) -> bool:
        if self._mediaType == MediaType.VIDEO:
            return True
        return False

    def isAudio(self) -> bool:
        if self._mediaType == MediaType.AUDIO:
            return True
        return False


class BasicInfo(Structure):
    _fields_ = [("ok", c_bool), ("duration", c_int64), ("bit_rate", c_int64), ("mime_type", c_char_p), ("type_long_name", c_char_p),
                ("type_name", c_char_p), ("get_stream_info_ok", c_bool), ("stream_list", POINTER(StreamInfo)), ("stream_list_length", c_size_t)]


class BasicInfoC:
    def __init__(self, data: BasicInfo, lib):
        self._lib: RSSBotLib = lib
        self._duration = data.duration if data.duration > 0 else None
        self._bitRate = data.bit_rate if data.bit_rate > 0 else None
        self._mimeType = data.mime_type.decode() if data.mime_type is not None else None
        self._typeLongName = data.type_long_name.decode(
        ) if data.type_long_name is not None else None
        self._typeName = data.type_name.decode() if data.type_name is not None else None
        self._getStreamInfoOk = data.get_stream_info_ok
        self._streamListLength = max(data.stream_list_length, 0)
        if self._streamListLength == 0 or not self._getStreamInfoOk:
            self._streamList = []
        else:
            self._streamList = []
            for i in range(self._streamListLength):
                try:
                    self._streamList.append(StreamInfoC(
                        data.stream_list[i], self._lib))
                except:
                    self._streamListLength = i
                    break

    def getVideoWidth(self) -> int:
        if not self._getStreamInfoOk:
            return None
        for i in self._streamList:
            info: StreamInfoC = i
            if info.isVideo and info._width is not None:
                return info._width

    def getVideoHeight(self) -> int:
        if not self._getStreamInfoOk:
            return None
        for i in self._streamList:
            info: StreamInfoC = i
            if info.isVideo and info._height is not None:
                return info._height


class RSSBotLib:
    def __init__(self, lib: CDLL, m):
        self._lib = lib
        from rssbot import main
        self._main: main = m
        self.__getBasicInfo = self._lib.getBasicInfo
        self.__getBasicInfo.restype = BasicInfo

    def getBasicInfo(self, url: str) -> (bool, BasicInfoC):
        try:
            d: BasicInfo = self.__getBasicInfo(url.encode())
            if d.ok:
                return True, BasicInfoC(d, self)
            return False, None
        except:
            return False, None

    def addVideoInfo(self, url: str, data: dict, loc: str = None) -> AddVideoInfoResult:
        if loc is not None:
            re, info = self.getBasicInfo(loc)
            if not re:
                re, info = self.getBasicInfo(url)
        else:
            re, info = self.getBasicInfo(url)
        if not re:
            return AddVideoInfoResult.ERROR
        if info._typeName is not None and info._typeName == 'hls':
            return AddVideoInfoResult.IsHLS
        if info._duration is not None:
            data['duration'] = max(round(info._duration / (10 ** 6)), 1)
        if info.getVideoWidth() is not None:
            data['width'] = info.getVideoWidth()
        if info.getVideoHeight() is not None:
            data['height'] =info.getVideoHeight()
        return AddVideoInfoResult.OK


def loadRSSBotLib(loc: str, m):
    if loc is None:
        return None
    try:
        lib = CDLL(loc)
        return RSSBotLib(lib, m)
    except:
        return None
