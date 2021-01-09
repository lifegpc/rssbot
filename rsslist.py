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
from RSSEntry import RSSEntry, ChatEntry
from typing import List
from enum import Enum, unique
from math import ceil, floor
from textc import textc, timeToStr
from html import escape


@unique
class InlineKeyBoardForRSSList(Enum):
    FirstPage = 0
    LastPage = 1
    PrevPage = 2
    NextPage = 3
    Close = 4
    Content = 5
    BackToList = 6
    Unsubscribe = 7
    ConfirmUnsubscribe = 8
    CancleUnsubscribe = 9


def getTextContentForRSSInList(rssEntry: RSSEntry) -> str:
    text = textc()
    text.addtotext(
        f"""<a href="{rssEntry.url}">{escape(rssEntry.title)}</a>""")
    temp = '更新间隔：未知' if rssEntry.interval is None else f'更新间隔：{rssEntry.interval}分'
    text.addtotext(temp)
    temp = '上次更新时间：未知' if rssEntry.lastupdatetime is None or rssEntry.lastupdatetime < 0 else f'上次更新时间：{timeToStr(rssEntry.lastupdatetime)}'
    text.addtotext(temp)
    if len(rssEntry.chatList) > 0:
        chatEntry: ChatEntry = rssEntry.chatList[0]
        config = chatEntry.config
        text.addtotext("设置：")
        text.addtotext(f"禁用预览：{config.disable_web_page_preview}")
        text.addtotext(f"显示RSS标题：{config.show_RSS_title}")
        text.addtotext(f"显示内容标题：{config.show_Content_title}")
        text.addtotext(f"显示内容：{config.show_content}")
        text.addtotext(f"发送媒体：{config.send_media}")
    return text.tostr()


def getTextContentForRSSUnsubscribeInList(rssEntry: RSSEntry) -> str:
    return f"""你是否要取消订阅<a href="{rssEntry.url}">{escape(rssEntry.title)}</a>？"""


def getInlineKeyBoardForRSSList(chatId: int, RSSEntries: List[RSSEntry], page: int = 1, lastPage: bool = False, itemIndex: int = None) -> dict:
    d = []
    i = -1
    lineLimit = 7
    l = len(RSSEntries)
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
            rss = RSSEntries[s]
            d.append([])
            i = i + 1
            d[i].append(
                {'text': rss.title, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.Content.value},{s}'})
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


def getInlineKeyBoardForRSSInList(chatId: int, rssEntry: RSSEntry, index: int) -> dict:
    d = []
    i = -1
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '取消订阅', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.Unsubscribe.value},{index}'})
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '返回', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.BackToList.value},{index}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardForRSSUnsubscribeInList(chatId: int, rssEntry: RSSEntry, index: int) -> dict:
    d = []
    i = -1
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '是', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.ConfirmUnsubscribe.value},{index}'})
    d[i].append(
        {'text': '否', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.CancleUnsubscribe.value},{index}'})
    return {'inline_keyboard': d}
