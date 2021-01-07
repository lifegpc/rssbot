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
from RSSEntry import RSSEntry
from typing import List
from enum import Enum, unique
from math import ceil


@unique
class InlineKeyBoardForRSSList(Enum):
    FirstPage = 0
    LastPage = 1
    PrevPage = 2
    NextPage = 3
    Close = 4
    Content = 5


def getInlineKeyBoardForRSSList(chatId: int, RSSEntries: List[RSSEntry], page=1) -> dict:
    d = []
    i = -1
    lineLimit = 7
    l = len(RSSEntries)
    pn = ceil(l / lineLimit)
    if l != 0:
        page = max(min(pn, page), 1)
        s = max(lineLimit * (page - 1), 0)
        n = min(lineLimit * page, l)
        while s < n:
            rss = RSSEntries[s]
            d.append([])
            i = i + 1
            d[i].append({'text': rss.title[0:20],
                         'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.Content.value},{s}'})
            s = s + 1
        if pn != 1:
            d.append([])
            i = i + 1
            if page != 1:
                d[i].append(
                    {'text': '上一页', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.PrevPage.value},{page}'})
            if page != pn:
                d[i].append(
                    {'text': '下一页', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.NextPage.value},{page}'})
            d.append([])
            i = i + 1
            if page != 1:
                d[i].append(
                    {'text': '首页', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.FirstPage.value}'})
            if page != pn:
                d[i].append(
                    {'text': '尾页', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.LastPage.value}'})
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '关闭', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.Close.value}'})
    return {'inline_keyboard': d}
