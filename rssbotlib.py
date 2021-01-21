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
from ctypes import Structure, c_bool, c_int64, c_char_p, CDLL, c_ushort, c_uint16, c_int, POINTER, c_size_t, pointer
from enum import Enum, unique
from typing import List


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


class AVDictionaryEntry(Structure):
    _fields_ = [("key", c_char_p), ("value", c_char_p)]


class AVDictionary(Structure):
    _fields_ = [("count", c_int), ("elems", POINTER(AVDictionaryEntry))]


class AVDictionaryC:
    def __init__(self, data: POINTER(AVDictionary)):
        self.__dict = {}
        if not bool(data):
            return
        for i in range(data.contents.count):
            try:
                ele = data.contents.elems[i]
                if ele.key is not None:
                    self.__dict[ele.key.decode()] = ele.value.decode(
                    ) if ele.value is not None else None
            except:
                return

    def __getitem__(self, key: str):
        if key not in self.__dict:
            return None
        return self.__dict[key]

    def keys(self):
        return self.__dict.keys()

    def __str__(self):
        t = ''
        for k in self.__dict.keys():
            t = f'{t}{k}: {self.__dict[k]}'
        if t == '':
            t = 'No Data'
        return t


class AVRational(Structure):
    _fields_ = [("num", c_int), ("den", c_int)]


class AVRationalC:
    def __init__(self, data: AVRational):
        self._num = data.num
        self._den = data.den

    def cal(self):
        return self._num / self._den


class ChapterInfo(Structure):
    _fields_ = [("id", c_size_t), ("time_base", AVRational), ("start",
                                                              c_int64), ("end", c_int64), ("metadata", POINTER(AVDictionary))]


class ChapterInfoC:
    def __init__(self, data: ChapterInfo):
        self._id = data.id
        self._timeBase = AVRationalC(data.time_base)
        self._start = data.start
        self._end = data.end
        self._metadata = AVDictionaryC(data.metadata)


class StreamInfo(Structure):
    _fields_ = [("originMediaType", c_int), ("mediaType", c_int), ("originCodecID", c_int), ("codecID", c_int), ("bitRate", c_int64), ("bitsPerCodedSample", c_int), ("bitsPerRawSample",
                                                                                                                                                                      c_int), ("profile", c_int), ("level", c_int), ("width", c_int), ("height", c_int), ("channels", c_int), ("sampleRate", c_int), ("metadata", POINTER(AVDictionary))]


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
        self._metadata = AVDictionaryC(data.metadata)

    def getCodecDescription(self) -> str:
        return self._lib.getCodecDescription(self._originCodecID)

    def getCodecMimeType(self) -> List[str]:
        return self._lib.getCodecMimeType(self._originCodecID)

    def getCodecName(self) -> str:
        return self._lib.getCodecName(self._originCodecID)

    def getProfileName(self) -> str:
        return self._lib.getProfileName(self._originCodecID, self._profile)

    def isVideo(self) -> bool:
        if self._mediaType == MediaType.VIDEO:
            return True
        return False

    def isAudio(self) -> bool:
        if self._mediaType == MediaType.AUDIO:
            return True
        return False


class BasicInfo(Structure):
    _fields_ = [("ok", c_bool), ("duration", c_int64), ("bit_rate", c_int64), ("mime_type", c_char_p), ("type_long_name", c_char_p), ("type_name", c_char_p), ("get_stream_info_ok", c_bool),
                ("stream_list", POINTER(StreamInfo)), ("stream_list_length", c_size_t), ("metadata", POINTER(AVDictionary)), ("chapters", POINTER(ChapterInfo)), ("nb_chapters", c_size_t)]


class BasicInfoC:
    def __init__(self, data: BasicInfo, lib):
        self._lib: RSSBotLib = lib
        self._duration = data.duration if data.duration > 0 else None
        self._bitRate = data.bit_rate if data.bit_rate > 0 else None
        self._mimeType = data.mime_type.decode() if data.mime_type is not None else None
        self._typeLongName = data.type_long_name.decode(
        ) if data.type_long_name is not None else None
        self._typeName = data.type_name.decode() if data.type_name is not None else None
        self._metadata = AVDictionaryC(data.metadata)
        self._nbChapters = data.nb_chapters
        if self._nbChapters == 0:
            self._chapters = []
        else:
            self._chapters = []
            for i in range(self._nbChapters):
                try:
                    self._chapters.append(ChapterInfoC(data.chapters[i]))
                except:
                    self._nbChapters = i
                    break
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
        self.__getCodecDescription = self._lib.getCodecDescription
        self.__getCodecDescription.restype = c_char_p
        self.__getCodecMimeType = self._lib.getCodecMimeType
        self.__getCodecMimeType.restype = POINTER(c_char_p)
        self.__getCodecMimeType.argstype = [c_int, POINTER(c_size_t)]
        self.__getCodecName = self._lib.getCodecName
        self.__getCodecName.restype = c_char_p
        self.__getProfileName = self._lib.getProfileName
        self.__getProfileName.restype = c_char_p
        self.__timeBase = self._lib.getAVTIMEBASE()

    def getBasicInfo(self, url: str) -> (bool, BasicInfoC):
        try:
            d: BasicInfo = self.__getBasicInfo(url.encode())
            if d.ok:
                return True, BasicInfoC(d, self)
            return False, None
        except:
            return False, None

    def getCodecDescription(self, codecId: int) -> str:
        "codecId is originCodecId"
        if codecId is None:
            return None
        try:
            r = self.__getCodecDescription(codecId)
            if r is None:
                return None
            return r.decode()
        except:
            return None

    def getCodecMimeType(self, codecId: int) -> List[str]:
        "codecId is originCodecId"
        if codecId is None:
            return None
        try:
            l = c_size_t(0)
            pl = pointer(l)
            r = self.__getCodecMimeType(codecId, pl)
            if l.value == 0:
                return None
            t = []
            for i in range(l.value):
                t.append(r[i].decode())
            return t
        except:
            return None

    def getCodecName(self, codecId: int) -> str:
        "codecId is originCodecId"
        if codecId is None:
            return None
        try:
            r = self.__getCodecName(codecId)
            if r is None:
                return None
            return r.decode()
        except:
            return None

    def getProfileName(self, codecId: int, profile: int) -> str:
        "codecId is originCodecId"
        if codecId is None or profile is None:
            return None
        try:
            r = self.__getProfileName(codecId, profile)
            if r is None:
                return None
            return r.decode()
        except:
            return None

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
            data['duration'] = max(round(info._duration / self.__timeBase), 1)
        if info.getVideoWidth() is not None:
            data['width'] = info.getVideoWidth()
        if info.getVideoHeight() is not None:
            data['height'] = info.getVideoHeight()
        return AddVideoInfoResult.OK


def loadRSSBotLib(loc: str, m):
    if loc is None:
        return None
    try:
        lib = CDLL(loc)
        return RSSBotLib(lib, m)
    except:
        return None
