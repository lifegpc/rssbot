# (C) 2021-2022 lifegpc
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
from enum import Enum, unique
from html import escape
from math import ceil, floor
from typing import List
from config import RSSConfig
from readset import settings
from rssbotlib import have_rssbotlib
from RSSEntry import ChatEntry, RSSEntry
from textc import textc, timeToStr


@unique
class InlineKeyBoardForManage(Enum):
    Close = 0
    ManageByRSS = 1
    ManageByChatId = 2
    FirstPage = 3
    LastPage = 4
    PrevPage = 5
    NextPage = 6
    ManageMenu = 7
    RSSManage = 8
    ChatManage = 9
    BackToList = 10
    Unsubscribe = 11
    ConfirmUnsubscribe = 12


def getInlineKeyBoardForManage():
    d = []
    i = -1
    d.append([])
    i += 1
    d[i].append({'text': '按RSS管理', 'callback_data': f'3,{InlineKeyBoardForManage.ManageByRSS.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '按用户管理', 'callback_data': f'3,{InlineKeyBoardForManage.ManageByChatId.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '关闭', 'callback_data': f'3,{InlineKeyBoardForManage.Close.value}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardForManageRSSList(RSSEntries: List[RSSEntry], page: int = 1, lastPage: bool = False, itemIndex: int = None, base: str = None, back: str = None):
    d = []
    i = -1
    lineLimit = 7
    if base is None:
        base = f'3,{InlineKeyBoardForManage.ManageByRSS.value}'
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
            d[i].append({'text': rss.title, 'callback_data': f'{base},{InlineKeyBoardForManage.RSSManage.value},{s},{rss.id}'})
            s = s + 1
        if pn != 1:
            d.append([])
            i = i + 1
            if page != 1:
                d[i].append({'text': '上一页', 'callback_data': f'{base},{InlineKeyBoardForManage.PrevPage.value},{page}'})
            if page != pn:
                d[i].append({'text': '下一页', 'callback_data': f'{base},{InlineKeyBoardForManage.NextPage.value},{page}'})
            d.append([])
            i = i + 1
            if page != 1:
                d[i].append({'text': '首页', 'callback_data': f'{base},{InlineKeyBoardForManage.FirstPage.value}'})
            if page != pn:
                d[i].append({'text': '尾页', 'callback_data': f'{base},{InlineKeyBoardForManage.LastPage.value}'})
    d.append([])
    i = i + 1
    d[i].append({'text': '返回', 'callback_data': f'3,{InlineKeyBoardForManage.ManageMenu.value}' if back is None else back})
    return {'inline_keyboard': d}


def getInlineKeyBoardForManageChatList(m, chatList: List[int], page: int = 1, lastPage: bool = False, itemIndex: int = None):
    d = []
    i = -1
    lineLimit = 7
    base = f'3,{InlineKeyBoardForManage.ManageByChatId.value}'
    l = len(chatList)
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
            chat_id = chatList[s]
            d.append([])
            i = i + 1
            d[i].append({'text': m.getChatName(chat_id), 'callback_data': f'{base},{InlineKeyBoardForManage.ChatManage.value},{s},{chat_id}'})
            s = s + 1
        if pn != 1:
            d.append([])
            i = i + 1
            if page != 1:
                d[i].append({'text': '上一页', 'callback_data': f'{base},{InlineKeyBoardForManage.PrevPage.value},{page}'})
            if page != pn:
                d[i].append({'text': '下一页', 'callback_data': f'{base},{InlineKeyBoardForManage.NextPage.value},{page}'})
            d.append([])
            i = i + 1
            if page != 1:
                d[i].append({'text': '首页', 'callback_data': f'{base},{InlineKeyBoardForManage.FirstPage.value}'})
            if page != pn:
                d[i].append({'text': '尾页', 'callback_data': f'{base},{InlineKeyBoardForManage.LastPage.value}'})
    d.append([])
    i = i + 1
    d[i].append({'text': '返回', 'callback_data': f'3,{InlineKeyBoardForManage.ManageMenu.value}'})
    return {'inline_keyboard': d}


def getTextContentForRSSInManageList(m, rssEntry: RSSEntry, s: settings, chatId: int = None) -> str:
    text = textc()
    text.addtotext(
        f"""<a href="{rssEntry.url}">{rssEntry.title}</a>""")
    ttl = 0 if rssEntry.interval is None else rssEntry.interval
    ttl = max(min(ttl, s.maxTTL), s.minTTL)
    temp = f'更新间隔：{ttl}分'
    if rssEntry.lasterrortime is not None and rssEntry.lasterrortime >= rssEntry.lastupdatetime and rssEntry.errorcount > 0:
        temp = f'{temp}({s.retryTTL[rssEntry.errorcount]}分)'
    text.addtotext(temp)
    temp = '上次更新时间：未知' if rssEntry.lastupdatetime is None or rssEntry.lastupdatetime < 0 else f'上次更新时间：{timeToStr(rssEntry.lastupdatetime)}'
    text.addtotext(temp)
    if rssEntry.lasterrortime is not None:
        temp = f'上次更新失败时间：{timeToStr(rssEntry.lasterrortime)}'
        text.addtotext(temp)
    if rssEntry.errorcount > 0:
        temp = f'连续更新失败次数：{rssEntry.errorcount}'
        text.addtotext(temp)
    if chatId is not None:
        chatName = m.getChatName(chatId)
        temp = chatName if chatId < 0 else f'<a href="tg://user?id={chatId}">{escape(chatName)}</a>'
        text.addtotext(f'订阅用户：{temp}')
    if len(rssEntry.chatList) > 0 and chatId is not None:
        chatEntry: ChatEntry = rssEntry.chatList[0]
        config = chatEntry.config
        text.addtotext("设置：")
        text.addtotext(f"禁用预览：{config.disable_web_page_preview}")
        text.addtotext(f"显示RSS标题：{config.show_RSS_title}")
        text.addtotext(f"显示内容标题：{config.show_Content_title}")
        text.addtotext(f"显示内容：{config.show_content}")
        text.addtotext(f"发送媒体：{config.send_media}")
        text += f"单独一行显示链接：{config.display_entry_link}"
        text += f"发送图片为文件：{config.send_img_as_file}"
        if config.thread_ids.isEnabled:
            text += f"发送到默认话题：{config.thread_ids._without_id}"
            text += f"要发送到的话题ID列表："
            for i in config.thread_ids._list:
                text += f"{i}"
        else:
            text += "未启用发送到话题功能"
        if have_rssbotlib:
            text += f'发送原始像素格式的Pixiv动图：{config.send_ugoira_with_origin_pix_fmt}'
            text += f'发送Pixiv动图为{config.send_ugoira_method}'
            text += f"发送时压缩过大图片：{config.compress_big_image}"
        text += f"RSS全局设置："
        text += f"发送时使用原文件名：{config.send_origin_file_name}"
    else:
        global_config = RSSConfig(rssEntry._settings)
        text += f"RSS全局设置："
        text += f"发送时使用原文件名：{global_config.send_origin_file_name}"
    return text.tostr()


def getInlineKeyBoardForRSSInManageList(rss: RSSEntry, index: int, base: str, chatId: int = None, chatIndex: int = None, m = None, page: int = None, lastPage: bool = False):
    d = []
    i = -1
    d.append([])
    i += 1
    have_chat_id = chatId is not None and chatIndex is not None
    if have_chat_id:
        d[i].append({'text': '取消订阅', 'callback_data': f'{base},{InlineKeyBoardForManage.RSSManage.value},{index},{rss.id},{InlineKeyBoardForManage.Unsubscribe.value}'})
    else:
        from rssbot import main
        if m is None:
            raise ValueError('m must not be None.')
        m: main = m
        m._db.getRSSChatList(rss)
        lineLimit = 7
        chatCount = len(rss.chatList)
        pn = ceil(chatCount / lineLimit)
        if lastPage:
            page = pn
        if chatIndex is not None and chatIndex >= 0:
            page = floor(chatIndex / lineLimit) + 1
        if page is None:
            page = 1
        if chatCount != 0:
            page = max(min(pn, page), 1)
            s = max(lineLimit * (page - 1), 0)
            n = min(lineLimit * page, chatCount)
            while s < n:
                chat: ChatEntry = rss.chatList[s]
                d.append([])
                i = i + 1
                d[i].append({'text': m.getChatName(chat.chatId), 'callback_data': f'{base},{InlineKeyBoardForManage.RSSManage.value},{index},{rss.id},{InlineKeyBoardForManage.ChatManage.value},{s},{chat.chatId}' })
                s += 1
            if pn != 1:
                d.append([])
                i += 1
                if page != 1:
                    d[i].append({'text': '上一页', 'callback_data': f'{base},{InlineKeyBoardForManage.RSSManage.value},{index},{rss.id},{InlineKeyBoardForManage.PrevPage.value},{page}'})
                if page != pn:
                    d[i].append({'text': '下一页', 'callback_data': f'{base},{InlineKeyBoardForManage.RSSManage.value},{index},{rss.id},{InlineKeyBoardForManage.NextPage.value},{page}'})
                d.append([])
                i = i + 1
                if page != 1:
                    d[i].append({'text': '首页', 'callback_data': f'{base},{InlineKeyBoardForManage.RSSManage.value},{index},{rss.id},{InlineKeyBoardForManage.FirstPage.value}'})
                if page != pn:
                    d[i].append({'text': '尾页', 'callback_data': f'{base},{InlineKeyBoardForManage.RSSManage.value},{index},{rss.id},{InlineKeyBoardForManage.LastPage.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '返回', 'callback_data': f'{base},{InlineKeyBoardForManage.BackToList.value},{index}' })
    return {'inline_keyboard': d}


def getInlineKeyBoardForRSSUnsubscribeInManageList(rss: RSSEntry, index: int, chatId: int, chatIndex: int):
    d = []
    i = -1
    d.append([])
    i += 1
    base = f'3,{InlineKeyBoardForManage.ManageByChatId.value},{InlineKeyBoardForManage.ChatManage.value},{chatIndex},{chatId},{InlineKeyBoardForManage.RSSManage.value},{index},{rss.id}'
    d[i].append({'text': '是', 'callback_data': f'{base},{InlineKeyBoardForManage.ConfirmUnsubscribe.value}'})
    d[i].append({'text': '否', 'callback_data': base})
    return {'inline_keyboard': d}
