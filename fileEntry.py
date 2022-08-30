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
from urllib.parse import urlsplit, parse_qs
from os.path import abspath, splitext, getsize, exists, isdir, isfile, join, basename
from time import time_ns
from random import randint
from requests import get
from os import remove as removeFile, mkdir, listdir, removedirs
from typing import Dict, List
from threading import Lock
from config import RSSConfig


def remove(s: str):
    try:
        if not exists(s):
            return
        if isfile(s):
            removeFile(s)
        elif isdir(s):
            p = s if s[-1] in ['/', '\\'] else f"{s}/"
            for v in listdir(s):
                remove(f"{p}{v}")
            removedirs(s)
    except:
        remove(s)


class SubFileEntry:
    def __init__(self, path: str) -> None:
        self._path = path
        self._abspath = path
        self._fileExist = True if exists(self._path) else False
        if self._fileExist:
            self._fileSize = getsize(self._path)
        self._localURI = f"file://{self._path}" if self._path[0] == '/' else f"file:///{self._path}"
        self._f = None
        self._fullfn = basename(self._abspath)

    def delete(self):
        if not self._fileExist:
            return
        if self._f is not None and not self._f.closed:
            self._f.close()
        try:
            remove(self._path)
            self._fileExist = False
        except:
            pass

    def open(self) -> bool:
        if not self._fileExist:
            return False
        if self._f is not None and not self._f.closed:
            self._f.seek(0, 0)
            return True
        try:
            self._f = open(self._path, 'rb')
            return True
        except:
            return False


class FileEntry:
    def __init__(self, url: str, m, config: RSSConfig):
        if not exists('Temp'):
            mkdir('Temp')
        if not isdir('Temp'):
            remove('Temp')
            mkdir('Temp')
        from rssbot import main
        self._m: main = m
        self._config = config
        self._url = url
        self._usetempdir = False
        self._tempdir: str = None
        ph = urlsplit(url).path
        self._ext = splitext(ph)[1]
        is_rssproxy = ph.endswith('/RSSProxy') or ph.endswith('/RSSProxy/')
        if self._ext == '' and is_rssproxy:  # Support my own proxy link
            qs = parse_qs(urlsplit(url).query)
            if 't' in qs:
                self._ext = splitext(urlsplit(qs['t'][0]).path)[1]
        if self._ext == '':
            self._ext = '.temp'
        if self._config.send_origin_file_name:
            self._usetempdir = True
            self._tempdir = f"{time_ns()}{randint(0, 9999)}"
            if is_rssproxy:
                self._fn = basename(splitext(urlsplit(qs['t'][0]).path)[0])
            if self._fn is None or self._fn == '':
                self._fn = basename(splitext(ph)[0])
            if self._fn == '':
                self._usetempdir = False
                self._fn = self._tempdir
            else:
                self._fn = join(self._tempdir, self._fn)
        else:
            self._fn = f"{time_ns()}{randint(0, 9999)}"
        self._fullfn = f"{self._fn}{self._ext}"
        if self._usetempdir:
            self._tempdir = abspath(join('Temp', self._tempdir))
            mkdir(self._tempdir)
        self._abspath = abspath(f'Temp/{self._fn}{self._ext}')
        try:
            self._r = get(url, stream=True, timeout=self._m._setting.downloadTimeOut)
            if self._r.ok:
                with open(self._abspath, 'wb') as f:
                    for chunk in self._r.iter_content(1024):
                        if chunk:
                            f.write(chunk)
            self.ok = self._r.ok
        except:
            self.ok = False
        self._fileExist = True if exists(self._abspath) else False
        if not self._fileExist:
            self._fileSize = 0
            if self._usetempdir:
                remove(self._tempdir)
        else:
            self._fileSize = getsize(self._abspath)
        self._localURI = f"file://{self._abspath}" if self._abspath[0] == '/' else f"file:///{self._abspath}"
        self._f = None
        self._subFileDict: Dict[str, SubFileEntry] = {}

    def addSubFile(self, name: str, ext: str):
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError('At least 1 char.')
        if not isinstance(ext, str) or len(ext) == 0:
            ext = 'temp'
        na = f"{name}.{ext}"
        if na in self._subFileDict:
            return False
        p = self.getSubPath(name, ext)
        if not exists(p):
            raise FileNotFoundError(p)
        self._subFileDict[na] = SubFileEntry(p)
        return True

    def delete(self):
        for key in self._subFileDict:
            self._subFileDict[key].delete()
        self._subFileDict = {}
        if not self._fileExist:
            return
        if self._f is not None and not self._f.closed:
            self._f.close()
        try:
            remove(self._abspath)
            if self._usetempdir:
                remove(self._tempdir)
            self._fileExist = False
        except:
            pass

    def getSubFile(self, name: str, ext: str):
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError('At least 1 char.')
        if not isinstance(ext, str) or len(ext) == 0:
            ext = 'temp'
        na = f"{name}.{ext}"
        if na in self._subFileDict:
            return self._subFileDict[na]

    def getSubPath(self, name: str, ext: str):
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError('At least 1 char.')
        if not isinstance(ext, str) or len(ext) == 0:
            ext = 'temp'
        return splitext(self._abspath)[0] + name + '.' + ext

    def open(self) -> bool:
        if not self._fileExist:
            return False
        if self._f is not None and not self._f.closed:
            self._f.seek(0, 0)
            return True
        try:
            self._f = open(self._abspath, 'rb')
            return True
        except:
            return False


class FileEntries:
    def __init__(self, m):
        from rssbot import main
        self._m: main = m
        self.__list = []
        self._value_lock = Lock()

    def add(self, url: str, config: RSSConfig) -> FileEntry:
        if self.has(url):
            return self.get(url)
        fileEntry = FileEntry(url, self._m, config)
        if fileEntry.ok and fileEntry._fileExist:
            self.__list.append(fileEntry)
            return fileEntry
        return None

    def clear(self):
        with self._value_lock:
            for v in self.__list:
                fileEntry: FileEntry = v
                fileEntry.delete()
            i = 0
            while i < len(self.__list):
                fileEntry = self.__list[i]
                if not fileEntry._fileExist:
                    self.__list.remove(fileEntry)
                    i = i - 1
                i = i + 1

    def get(self, url: str) -> FileEntry:
        for v in self.__list:
            fileEntry: FileEntry = v
            if fileEntry._url == url:
                return fileEntry
        return None

    def getList(self) -> List[FileEntry]:
        r = []
        for v in self.__list:
            r.append(v)
        return r

    def has(self, url: str):
        for v in self.__list:
            fileEntry: FileEntry = v
            if fileEntry._url == url:
                return True
        return False
