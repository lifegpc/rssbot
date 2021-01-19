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
from typing import List
from getopt import getopt
from botOwner import BotOwnerList


class settings:
    def __init__(self, m, fn: str = None):
        from rssbot import main
        self._main: main = m
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
        self._maxCount = int(
            d['maxCount']) if 'maxCount' in d and d['maxCount'].isnumeric() else 100
        self._minTTL = int(d['minTTL']) if 'minTTL' in d and d['minTTL'].isnumeric(
        ) and int(d['minTTL']) >= 1 else 5
        self._maxTTL = int(d['maxTTL']) if 'maxTTL' in d and d['maxTTL'].isnumeric(
        ) and int(d['maxTTL']) >= self._minTTL else max(1440, self._minTTL)
        self._maxRetryCount = int(d['maxRetryCount']) if 'maxRetryCount' in d and d['maxRetryCount'].isnumeric(
        ) and int(d['maxRetryCount']) >= 0 else 3
        self._telegramBotApiServer = d['telegramBotApiServer'] if 'telegramBotApiServer' in d else 'https://api.telegram.org'
        self._downloadMediaFile = bool(int(
            d['downloadMediaFile'])) if 'downloadMediaFile' in d and d['downloadMediaFile'].isnumeric() else False
        self._sendFileURLScheme = bool(int(
            d['sendFileURLScheme'])) if 'sendFileURLScheme' in d and d['sendFileURLScheme'].isnumeric() else False
        self._rssbotLib = d['rssbotLib'] if 'rssbotLib' in d and d['rssbotLib'] != '' else None
        self._databaseLocation = d['databaseLocation'] if 'databaseLocation' in d and d['databaseLocation'] != '' else 'data.db'
        self._retryTTL = int(d['retryTTL']) if 'retryTTL' in d and d['retryTTL'].isnumeric(
        ) and int(d['retryTTL']) > 0 else 30
        self._botOwnerList = BotOwnerList(
            self._main, d['botOwnerList']) if 'botOwnerList' in d and d['botOwnerList'] != '' else BotOwnerList(self._main)


class commandline:
    def __init__(self, commandline: List[str] = None):
        self._config = 'settings.txt'
        self._rebuildHashlist = False
        self._exitAfterRebuild = False
        if commandline is not None:
            self.parse(commandline)

    def parse(self, commandline: List[str]):
        cml = getopt(commandline, 'c:', ['rebuild-hashlist', 'exit-after-rebuild', 'config='])
        for i in cml[0]:
            if i[0] in ['-c', '--config']:
                self._config = i[1]
            if i[0] == '--rebuild-hashlist':
                self._rebuildHashlist = True
            if i[0] == '--exit-after-rebuild':
                self._exitAfterRebuild = True
