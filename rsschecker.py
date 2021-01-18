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
from threading import Thread
from time import sleep, time
from RSSEntry import RSSEntry, calHash, ChatEntry, HashEntries
from traceback import format_exc
from rssparser import RSSParser
from os import _exit


class RSSCheckerThread(Thread):
    def __loop(self):
        for rss in self._main._db.getAllRSSList():
            if self.__needUpdate(rss) or self._main._commandLine._rebuildHashlist:
                try:
                    p = RSSParser()
                    p.parse(rss.url)
                    updateTime = int(time())
                    if p.check():
                        meta = p.m
                        itemList = p.itemList[:self._main._setting._maxCount]
                        itemList.reverse()
                        if self._main._commandLine._rebuildHashlist:
                            rss.hashList = HashEntries(
                                self._main._setting._maxCount)
                        for item in itemList:
                            hashEntry = calHash(rss.url, item)
                            if self._main._commandLine._rebuildHashlist:
                                rss.hashList.add(hashEntry)
                                continue
                            if not rss.hashList.has(hashEntry):
                                rss.hashList.add(hashEntry)
                                for info in rss.chatList:
                                    chatEntry: ChatEntry = info
                                    try:
                                        for i in range(self._main._setting._maxRetryCount + 1):
                                            suc, text = self._main._sendMessage(
                                                chatEntry.chatId, meta, item, chatEntry.config, True)
                                            if suc:
                                                break
                                            sleep(5)
                                            if i < self._main._setting._maxRetryCount:
                                                print(f'开始第{i+i}次重试\n{text}')
                                            else:
                                                text2 = f'\n{rss.title}'
                                                if 'link' in item:
                                                    text2 = f"{text2}\n{item['link']}"
                                                self._main._request('sendMessage', 'post', {
                                                                    'chat_id': chatEntry.chatId, 'text': f'已尝试重发{i}次，发送失败。\n{text}{text2}'})
                                    except:
                                        print(format_exc())
                    else:
                        raise ValueError('Unknown RSS.')
                    self._main._db.updateRSS(
                        rss.title, rss.url, updateTime, rss.hashList, p.ttl)
                except:
                    print(format_exc())
                    self._main._db.updateRSSWithError(rss.url, int(time()))
        if self._main._commandLine._rebuildHashlist and self._main._commandLine._exitAfterRebuild:
            _exit(0)
        self._main._commandLine._rebuildHashlist = False
        self._main._tempFileEntries.clear()

    def __init__(self, m):
        Thread.__init__(self)
        from rssbot import main
        self._main: main = m

    def __needUpdate(self, rss: RSSEntry):
        if rss.lasterrortime is not None and rss.lasterrortime >= rss.lastupdatetime:
            return True if int(time()) > rss.lasterrortime + self._main._setting._retryTTL * 60 else False
        if rss.lastupdatetime is None:
            return True
        TTL = self._main._setting._minTTL
        if rss.interval is not None:
            TTL = max(min(rss.interval, self._main._setting._maxTTL),
                      self._main._setting._minTTL)
        TTL = TTL * 60
        return True if int(time()) > rss.lastupdatetime + TTL else False

    def run(self):
        while True:
            try:
                self.__loop()
            except:
                print(format_exc())
            sleep(1)
