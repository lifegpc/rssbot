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
from re import search
from typing import List
from textc import textc, timeToStr
from enum import Enum, unique
from math import ceil, floor


class BlackInfo:
    __uid: int = None
    op_uid: int = None
    from_config: bool = False
    add_time: int = None
    reason: str = None

    @property
    def uid(self) -> int:
        return self.__uid

    def __init__(self, uid: int, op_uid: int = None, add_time: int = None, reason: str = None, title: str = None):
        self.__uid = uid
        self.op_uid = op_uid
        self.from_config = True if self.op_uid is None else False
        self.add_time = add_time
        self.reason = reason
        self.title = title

    @property
    def name(self) -> str:
        return f"{self.uid}" if self.title is None else self.title


class BlackInfoListIter:
    def __init__(self, li: List[BlackInfo]):
        self.__l = li
        self.__start = 0

    def __next__(self) -> BlackInfo:
        if self.__start >= len(self.__l):
            raise StopIteration
        v = self.__l[self.__start]
        self.__start += 1
        return v


class BlackInfoList:
    def __add__(self, b):
        o = BlackInfoList(self.__l)
        if isinstance(b, (BlackInfoList, list)):
            for i in b:
                o.append(i)
        elif isinstance(b, BlackInfo):
            o.append(b)
        return o

    def __getitem__(self, i) -> BlackInfo:
        return self.__l[i]

    def __iadd__(self, b):
        if isinstance(b, (BlackInfoList, list)):
            for i in b:
                self.append(i)
        elif isinstance(b, BlackInfo):
            self.append(b)
        return self

    def __init__(self, li: List[BlackInfo] = None):
        self.__t = []
        self.__l = []
        if li is not None:
            for i in li:
                self.append(i)

    def __iter__(self):
        it = BlackInfoListIter(self.__l)
        return it

    def __len__(self):
        return len(self.__l)

    def append(self, info: BlackInfo):
        if info.uid not in self.__t:
            self.__l.append(info)
            self.__t.append(info.uid)

    def find(self, uid: int):
        if uid in self.__t:
            return self.__t.index(uid)
        else:
            return -1

    def isInBlackList(self, chatId: int) -> bool:
        return chatId in self.__t


class ConfigBlackList:
    def __init__(self, m, s: str = None):
        from rssbot import main
        self._main: main = m
        self.__list = []
        if s is not None:
            l = s.split(',')
            for i in l:
                if search(r'^[\+-]?[0-9]+$', i) is not None:
                    self.__list.append(int(i))

    def getBlackList(self) -> BlackInfoList:
        r = BlackInfoList()
        for i in self.__list:
            r.append(BlackInfo(i))
        return r

    def isInBlackList(self, chatId: int) -> bool:
        return chatId in self.__list


class BlackList:
    def __init__(self, m):
        from rssbot import main
        self._main: main = m
        self._configBlackList = ConfigBlackList(m, self._main._setting._blackList)
        self._blackList = self._main._db.getBlackList()

    def ban(self, i: BlackInfo):
        re = self._main._db.addBlackInfo(i)
        if re:
            self._blackList = self._main._db.getBlackList()
            self.checkRSSList()
        return re

    def getBlackList(self) -> BlackInfoList:
        r = self._configBlackList.getBlackList()
        r += self._blackList
        return r

    def isInBlackList(self, chatId: int) -> bool:
        if self._configBlackList.isInBlackList(chatId):
            return True
        if self._blackList.isInBlackList(chatId):
            return True
        return False

    def checkRSSList(self):
        li = self.getBlackList()
        for i in li:
            self._main._db.removeChatInChatList(i.uid)

    def unban(self, userId: int):
        re = self._main._db.removeFromBlackList(userId)
        if re:
            self._blackList = self._main._db.getBlackList()
        return re


@unique
class InlineKeyBoardForBlackList(Enum):
    FirstPage = 0
    LastPage = 1
    PrevPage = 2
    NextPage = 3
    Close = 4
    BlackInfo = 5
    BackToList = 6
    Unban = 7
    ConfirmUnban = 8
    CancleUnban = 9


def getTextContentForBlackInfo(i: BlackInfo):
    t = textc()
    link = '' if i.uid < 0 else f'tg://user?id={i.uid}'
    t += f'被封禁用户: <a href="{link}">{i.name}</a>'
    if i.from_config:
        t += '来源：配置文件'
    else:
        t += '来源：数据库'
        t += f'封禁操作人：<a href="tg://user?id={i.op_uid}">{i.op_uid}</a>'
        t += f'封禁时间：{timeToStr(i.add_time)}'
        t += f'封禁理由：{i.reason}'
    return t.tostr()


def getTextContentForUnbanBlackInfo(i: BlackInfo):
    link = '' if i.uid < 0 else f'tg://user?id={i.uid}'
    return f'是否要取消封禁<a href="{link}">{i.name}</a>？'


def getInlineKeyBoardForBlackList(bl: BlackInfoList, page: int = 1, lastPage: bool = False, itemIndex: int = None):
    d = []
    i = -1
    lineLimit = 7
    l = len(bl)
    pn = ceil(l / lineLimit)
    if lastPage:
        page = pn
    if itemIndex is not None and itemIndex >= 0:
        page = floor(itemIndex / lineLimit) + 1
    if l != 0:
        page = max(min(pn, page), 1)
        s = max(lineLimit * (page - 1), 0)
        n = min(lineLimit * page, l)
        while s < n:
            d.append([])
            i += 1
            d[i].append({'text': bl[s].name, 'callback_data': f'2,{InlineKeyBoardForBlackList.BlackInfo.value},{s},{bl[s].uid}'})
            s += 1
        if pn != 1:
            d.append([])
            i += 1
            if page != 1:
                d[i].append({'text': '上一页', 'callback_data': f'2,{InlineKeyBoardForBlackList.PrevPage.value},{page}'})
            if page != pn:
                d[i].append({'text': '下一页', 'callback_data': f'2,{InlineKeyBoardForBlackList.NextPage.value},{page}'})
            d.append([])
            i += 1
            if page != 1:
                d[i].append({'text': '首页', 'callback_data': f'2,{InlineKeyBoardForBlackList.FirstPage.value}'})
            if page != pn:
                d[i].append({'text': '尾页', 'callback_data': f'2,{InlineKeyBoardForBlackList.LastPage.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '关闭', 'callback_data': f'2,{InlineKeyBoardForBlackList.Close.value}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardForBlackInfo(b: BlackInfo, index: int):
    d = []
    i = -1
    if not b.from_config:
        d.append([])
        i += 1
        d[i].append({'text': '取消封禁', 'callback_data': f'2,{InlineKeyBoardForBlackList.Unban.value},{index},{b.uid}'})
    d.append([])
    i += 1
    d[i].append(
        {'text': '返回', 'callback_data': f'2,{InlineKeyBoardForBlackList.BackToList.value},{index}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardForUnbanBlackInfo(b: BlackInfo, index: int):
    d = []
    i = -1
    d.append([])
    i += 1
    d[i].append({'text': '是', 'callback_data': f'2,{InlineKeyBoardForBlackList.ConfirmUnban.value},{index},{b.uid}'})
    d[i].append({'text': '否', 'callback_data': f'2,{InlineKeyBoardForBlackList.CancleUnban.value},{index},{b.uid}'})
    return {'inline_keyboard': d}
