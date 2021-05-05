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
from urllib.parse import urlsplit
from os.path import abspath, splitext, getsize, exists, isdir, isfile
from time import time_ns
from random import randint
from requests import get
from os import remove as removeFile, mkdir, listdir, removedirs
from typing import List
from threading import Lock


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


class FileEntry:
    def __init__(self, url: str):
        if not exists('Temp'):
            mkdir('Temp')
        if not isdir('Temp'):
            remove('Temp')
            mkdir('Temp')
        self._url = url
        self._ext = splitext(urlsplit(url).path)[1]
        if self._ext == '':
            self._ext = '.temp'
        self._fn = f"{time_ns()}{randint(0, 9999)}"
        self._fullfn = f"{self._fn}{self._ext}"
        self._abspath = abspath(f'Temp/{self._fn}{self._ext}')
        try:
            self._r = get(url, stream=True)
            if self._r.ok:
                with open(self._abspath, 'wb') as f:
                    for chunk in self._r.iter_content(1024):
                        if chunk:
                            f.write(chunk)
            self.ok = self._r.ok
        except:
            self.ok = False
        self._fileSize = getsize(self._abspath)
        self._fileExist = True if exists(self._abspath) else False
        self._localURI = f"file://{self._abspath}" if self._abspath[0] == '/' else f"file:///{self._abspath}"
        self._f = None

    def delete(self):
        if not self._fileExist:
            return
        if self._f is not None and not self._f.closed:
            self._f.close()
        try:
            remove(self._abspath)
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
            self._f = open(self._abspath, 'rb')
            return True
        except:
            return False


class FileEntries:
    def __init__(self):
        self.__list = []
        self._value_lock = Lock()

    def add(self, url: str) -> FileEntry:
        if self.has(url):
            return self.get(url)
        fileEntry = FileEntry(url)
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
