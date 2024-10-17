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
from config import SendUgoiraMethod
from textc import textc, timeToStr
from readset import settings
from rssbotlib import have_rssbotlib


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
    SettingsPage = 10
    BackToContentPage = 11
    DisableWebPagePreview = 12
    ShowRSSTitle = 13
    ShowContentTitle = 14
    ShowContent = 15
    SendMedia = 16
    ForceUpdate = 17
    DisplayEntryLink = 18
    SendImgAsFile = 19
    GlobalSettingsPage = 20
    SendOriginFileName = 21
    SendUgoiraWithOriginPixFmt = 22
    SendUgoiraMethod = 23
    CompressBigImage = 24
    EnableTopic = 25
    AddTopicToList = 26
    EnableSendWithoutTopicId = 27
    RemoveTopicFromList = 28
    DisableTopic = 29
    AddAuthor = 30
    SetInterval = 31


def getTextContentForRSSInList(rssEntry: RSSEntry, s: settings) -> str:
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
    if len(rssEntry.chatList) > 0:
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
        text += f"添加作者名：{config.add_author}"
        text += f"RSS全局设置："
        text += f"发送时使用原文件名：{config.send_origin_file_name}"
        ttlt = '未设置' if config.interval is None else f"{config.interval}分"
        text += f"更新间隔：{ttlt}"
    return text.tostr()


def getTextContentForRSSUnsubscribeInList(rssEntry: RSSEntry) -> str:
    return f"""你是否要取消订阅<a href="{rssEntry.url}">{rssEntry.title}</a>？"""


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
                {'text': rss.title, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.Content.value},{s},{rss.id}'})
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


def getInlineKeyBoardForRSSInList(chatId: int, rssEntry: RSSEntry, index: int, isOwner: bool = False) -> dict:
    d = []
    i = -1
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '取消订阅', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.Unsubscribe.value},{index},{rssEntry.id}'})
    if not rssEntry.forceupdate and isOwner:
        d.append([])
        i = i + 1
        d[i].append(
            {'text': '强制更新', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.ForceUpdate.value},{index},{rssEntry.id}'})
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '设置', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SettingsPage.value},{index},{rssEntry.id}'})
    if isOwner:
        d.append([])
        i += 1
        d[i].append({'text': 'RSS全局设置', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.GlobalSettingsPage.value},{index},{rssEntry.id}'})
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
        {'text': '是', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.ConfirmUnsubscribe.value},{index},{rssEntry.id}'})
    d[i].append(
        {'text': '否', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.CancleUnsubscribe.value},{index},{rssEntry.id}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardForRSSSettingsInList(chatId: int, rssEntry: RSSEntry, index: int, page: int = 1) -> dict:
    d = []
    i = -1
    if page != 1:
        page = 1
    chatInfo: ChatEntry = rssEntry.chatList[0]
    config = chatInfo.config
    if page == 1:
        d.append([])
        i = i + 1
        temp = '启用预览' if config.disable_web_page_preview else '禁用预览'
        d[i].append(
            {'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.DisableWebPagePreview.value},{index},{rssEntry.id}'})
        temp = '隐藏RSS标题' if config.show_RSS_title else '显示RSS标题'
        d[i].append(
            {'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.ShowRSSTitle.value},{index},{rssEntry.id}'})
        d.append([])
        i = i + 1
        temp = '隐藏内容标题' if config.show_Content_title else '显示内容标题'
        d[i].append(
            {'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.ShowContentTitle.value},{index},{rssEntry.id}'})
        temp = '隐藏内容' if config.show_content else '显示内容'
        d[i].append(
            {'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.ShowContent.value},{index},{rssEntry.id}'})
        d.append([])
        i = i + 1
        temp = '禁用发送媒体' if config.send_media else '启用发送媒体'
        d[i].append(
            {'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SendMedia.value},{index},{rssEntry.id}'})
        temp = '禁用单独一行显示链接' if config.display_entry_link else '启用单独一行显示链接'
        d[i].append({'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.DisplayEntryLink.value},{index},{rssEntry.id}'})
        d.append([])
        i += 1
        temp = '禁用发送图片为文件' if config.send_img_as_file else '启用发送图片为文件'
        d[i].append({'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SendImgAsFile.value},{index},{rssEntry.id}'})
        if have_rssbotlib:
            temp = f"{'禁用' if config.send_ugoira_with_origin_pix_fmt else '启用'}发送原始像素格式的Pixiv动图"
            d[i].append({'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SendUgoiraWithOriginPixFmt.value},{index},{rssEntry.id}'})
            d.append([])
            i += 1
            temp2 = SendUgoiraMethod((config.send_ugoira_method.value + 1) % 4)
            temp = f'发送Pixiv动图为{temp2}'
            d[i].append({'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SendUgoiraMethod.value},{index},{rssEntry.id},{temp2.value}'})
            temp = f"{'禁用' if config.compress_big_image else '启用'}压缩过大图片"
            d[i].append({'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.CompressBigImage.value},{index},{rssEntry.id}'})
        d.append([])
        i += 1
        d[i].append({'text': f'{"管理" if config.thread_ids.isEnabled else "启用"}发送到话题功能', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.EnableTopic.value},{index},{rssEntry.id}'})
        d[i].append({'text': f'{"禁用" if config.add_author else "启用"}添加作者名', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.AddAuthor.value},{index},{rssEntry.id}'})
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '返回', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.BackToContentPage.value},{index},{rssEntry.id}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardForRSSThreadIdsInList(chatId: int, rssEntry: RSSEntry, index: int) -> dict:
    config = rssEntry.chatList[0].config
    d = [[]]
    i = 0
    d[i].append({'text': '添加新的话题', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.AddTopicToList.value},{index},{rssEntry.id}'})
    if config.thread_ids.isEnabled:
        d.append([])
        i += 1
        temp = f"{'禁用' if config.thread_ids._without_id else '启用'}发送到默认话题"
        d[i].append({'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.EnableSendWithoutTopicId.value},{index},{rssEntry.id}'})
        d.append([])
        i += 1
        d[i].append({'text': '移除已有的话题', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.RemoveTopicFromList.value},{index},{rssEntry.id}'})
        d.append([])
        i += 1
        d[i].append({'text': '禁用发送到话题功能', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.DisableTopic.value},{index},{rssEntry.id}'})
    d.append([])
    i += 1
    d[i].append({'text': '返回', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SettingsPage.value},{index},{rssEntry.id}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardForRSSGlobalSettingsInList(chatId: int, rssEntry: RSSEntry, index: int, page: int = 1) -> dict:
    d = []
    i = -1
    if page != 1:
        page = 1
    chatInfo: ChatEntry = rssEntry.chatList[0]
    config = chatInfo.config
    if page == 1:
        temp = '禁用发送时使用原文件名' if config.send_origin_file_name else '启用发送时使用原文件名'
        d.append([])
        i += 1
        d[i].append({'text': temp, 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SendOriginFileName.value},{index},{rssEntry.id}'})
        d.append([])
        i += 1
        d[i].append({'text': '设置更新间隔', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.SetInterval.value},{index},{rssEntry.id}'})
    d.append([])
    i += 1
    d[i].append({'text': '返回', 'callback_data': f'1,{chatId},{InlineKeyBoardForRSSList.BackToContentPage.value},{index},{rssEntry.id}'})
    return {'inline_keyboard': d}
