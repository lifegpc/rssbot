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
from typing import Optional, Tuple
try:
    import platform
    if platform.system() == "Windows":
        import sys
        if sys.version_info.major >= 3 and sys.version_info.minor >= 8:
            import os
            p = os.environ.get("RSSBOTLIB_DEP_PATH")
            if p is not None:
                for p in p.split(';'):
                    os.add_dll_directory(p)
    from _rssbotlib import version, VideoInfo, convert_ugoira_to_mp4, AVDict, convert_to_tg_thumbnail, tg_image_compress
    have_rssbotlib = True
except ImportError:
    have_rssbotlib = False
if have_rssbotlib:
    from fileEntry import FileEntry, SubFileEntry, remove


@unique
class AddVideoInfoResult(Enum):
    OK = 0
    ERROR = 1
    IsHLS = 2


if have_rssbotlib:
    class RSSBotLib:
        def __init__(self, m):
            from rssbot import main, MAX_PHOTO_SIZE
            self._main: main = m
            self._max_photo_size = MAX_PHOTO_SIZE
            self._version = version()
            if self._version is None or self._version >= [1, 2, 0, 0] or self._version < [1, 1, 0, 0]:
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

        def convert_ugoira_to_mp4(self, f: FileEntry, frames, force_yuv420p: bool):
            try:
                na = '_yuv420p' if force_yuv420p else '_origin'
                if f.getSubFile(na, 'mp4') is not None:
                    return True
                dst = f.getSubPath(na, 'mp4')
                opt = AVDict()
                if force_yuv420p:
                    opt['force_yuv420p'] = ''
                if not convert_ugoira_to_mp4(f._abspath, dst, frames, opts=opt):
                    return False
                f.addSubFile(na, 'mp4')
                return True
            except Exception:
                print_exc()
                try:
                    remove(dst)
                except Exception:
                    print_exc()
                return False

        def convert_to_tg_thumbnail(self, f: FileEntry, format: str = 'webp') -> bool:
            try:
                if f.getSubFile('_thumbnail', format) is not None:
                    return True
                dst = f.getSubPath('_thumbnail', format)
                if not convert_to_tg_thumbnail(f._abspath, dst, format):
                    return False
                f.addSubFile('_thumbnail', format)
                return True
            except Exception:
                print_exc()
                try:
                    remove(dst)
                except Exception:
                    print_exc()
                return False

        def compress_image(self, f: FileEntry, format: str = 'jpeg', max_len: int = 1920, force_yuv420p: bool = True) -> Optional[SubFileEntry]:
            try:
                na = f'_compressed_{max_len}' if force_yuv420p else f'_compressed_origin_{max_len}'
                if f.getSubFile(na, format) is not None:
                    return f.getSubFile(na, format)
                dst = f.getSubPath(na, format)
                opt = AVDict()
                if not force_yuv420p:
                    opt['force_yuv420p'] = '0'
                if not tg_image_compress(f._abspath, dst, format, max_len, opt):
                    return None
                f.addSubFile(na, format)
                return f.getSubFile(na, format)
            except Exception:
                print_exc()
                try:
                    remove(dst)
                except Exception:
                    print_exc()
                return None

        def is_supported_photo(self, f: FileEntry) -> Optional[Tuple[bool, bool]]:
            """
            第一个返回是否符合TG图片的要求
            第二个返回图片解析度过大时返回True
            """
            try:
                v = VideoInfo()
                if not v.parse(f._abspath):
                    return None
                streams = v.streams
                width = None
                height = None
                for stream in streams:
                    if stream.is_video:
                        width = stream.width
                        height = stream.height
                        break
                if width is None or height is None:
                    return None
                if width / height >= 20 or height / width >= 20:
                    return False, False
                elif width + height >= 10000 or f._fileSize >= self._max_photo_size:
                    return False, True
                else:
                    return True, False
            except Exception:
                print_exc()
                return None


def loadRSSBotLib(m):
    if have_rssbotlib:
        return RSSBotLib(m)
    else:
        return None
