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
from config import SendUgoiraMethod
from database import database, userStatus, RSSConfig
from RSSEntry import HashEntry, HashEntries, calHash, ChatEntry
from os.path import exists
from readset import settings, commandline
from requests import Session
from traceback import format_exc
from threading import Thread
from typing import List, Optional
from rssparser import RSSParser
from html import escape
from hashl import md5WithBase64
from enum import Enum, unique
from rsstempdict import rssMetaInfo, rssMetaList
from random import randrange
from textc import textc, removeEmptyLine, decodeURI
from re import search, I
from rsschecker import RSSCheckerThread
from rsslist import (
    getInlineKeyBoardForRSSList,
    InlineKeyBoardForRSSList,
    getInlineKeyBoardForRSSInList,
    getTextContentForRSSInList,
    getInlineKeyBoardForRSSUnsubscribeInList,
    getTextContentForRSSUnsubscribeInList,
    getInlineKeyBoardForRSSSettingsInList,
    getInlineKeyBoardForRSSGlobalSettingsInList,
    getInlineKeyBoardForRSSThreadIdsInList,
)
from usercheck import checkUserPermissionsInChat, UserPermissionsInChatCheckResult
import sys
from fileEntry import FileEntries, remove
from dictdeal import json2data
from rssbotlib import loadRSSBotLib, AddVideoInfoResult, have_rssbotlib
from time import sleep, time
from miraiDatabase import MiraiDatabase
from mirai import Mirai
from blackList import BlackList, InlineKeyBoardForBlackList, getInlineKeyBoardForBlackList, getTextContentForBlackInfo, getInlineKeyBoardForBlackInfo, getTextContentForUnbanBlackInfo, getInlineKeyBoardForUnbanBlackInfo, BlackInfo
from json import loads
from manage import getInlineKeyBoardForManage, InlineKeyBoardForManage, getInlineKeyBoardForManageRSSList, getInlineKeyBoardForManageChatList, getTextContentForRSSInManageList, getInlineKeyBoardForRSSInManageList, getInlineKeyBoardForRSSUnsubscribeInManageList


MAX_ITEM_IN_MEDIA_GROUP = 10
MAX_PHOTO_SIZE = 10485760
MAX_ANIMATION_SIZE = 52428800


def getMediaInfo(m: dict, config: RSSConfig = RSSConfig()) -> str:
    s = ''
    if 'link' in m:
        s = f"""{s}标题：<a href="{m['link']}">{m['title']}</a>"""
    else:
        s = f"{s}标题：{m['title']}"
    if 'description' in m:
        s = f"{s}\n描述：{escape(m['description'])}"
    if 'ttl' in m and m['ttl'] is not None:
        s = f"{s}\n更新间隔：{m['ttl']}分"
    else:
        s = f"{s}\n更新间隔：未知"
    if 'chatId' in m and m['chatId'] is not None:
        s = f"""{s}\n群/频道ID：{m['chatId']}"""
    elif 'userId' in m and m['userId'] is not None:
        s = f"""{s}\n<a href="tg://user?id={m['userId']}">订阅的账号</a>"""
    if '_type' in m and m['_type'] is not None:
        s = f"""{s}\n类型：{m['_type']}"""
    s = f"{s}\n设置："
    s = f"{s}\n禁用预览：{config.disable_web_page_preview}"
    s = f"{s}\n显示RSS标题：{config.show_RSS_title}"
    s = f"{s}\n显示内容标题：{config.show_Content_title}"
    s = f"{s}\n显示内容：{config.show_content}"
    s = f"{s}\n发送媒体：{config.send_media}"
    s = f"{s}\n单独一行显示链接：{config.display_entry_link}"
    s += f"\n发送图片为文件：{config.send_img_as_file}"
    if config.thread_ids.isEnabled:
        s += f"\n发送到默认话题：{config.thread_ids._without_id}"
        s += f"\n要发送到的话题ID列表："
        for i in config.thread_ids._list:
            s += f"\n{i}"
    else:
        s += "\n未启用发送到话题功能"
    if have_rssbotlib:
        s += f"\n发送原始像素格式的Pixiv动图：{config.send_ugoira_with_origin_pix_fmt}"
        s += f'\n发送Pixiv动图为{config.send_ugoira_method}'
        s += f"\n发送时压缩过大图片：{config.compress_big_image}"
    s += f"\nRSS全局设置："
    s += f"\n发送时使用原文件名：{config.send_origin_file_name}"
    return s


@unique
class InlineKeyBoardCallBack(Enum):
    Subscribe = 0
    SendPriview = 1
    ModifyChatId = 2
    BackUserId = 3
    SettingsPage = 4
    BackToNormalPage = 5
    DisableWebPagePreview = 6
    ShowRSSTitle = 7
    ShowContentTitle = 8
    ShowContent = 9
    SendMedia = 10
    DisplayEntryLink = 11
    SendImgAsFile = 12
    GlobalSettingsPage = 13
    SendOriginFileName = 14
    SendUgoiraWithOriginPixFmt = 15
    SendUgoiraMethod = 16
    CompressBigImage = 17
    EnableTopic = 18
    AddTopicToList = 19
    EnableSendWithoutTopicId = 20
    RemoveTopicFromList = 21
    DisableTopic = 22


def getInlineKeyBoardWhenRSS(hashd: str, m: dict, isOwn: bool) -> dict:
    d = []
    i = 0
    d.append([])
    d[i].append(
        {'text': '订阅', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.Subscribe.value}'})
    d[i].append(
        {'text': '发送示例消息', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SendPriview.value}'})
    if 'chatId' in m and m['chatId'] is not None:
        d.append([])
        i = i + 1
        d[i].append(
            {'text': '修改群组/频道ID', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.ModifyChatId.value}'})
        if 'userId' in m and m['userId'] is not None:
            d[i].append(
                {'text': '发送至私聊', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.BackUserId.value}'})
    elif 'userId' in m and m['userId'] is not None:
        d.append([])
        i = i + 1
        d[i].append(
            {'text': '发送至群组/频道', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.ModifyChatId.value}'})
    d.append([])
    i = i + 1
    d[i].append(
        {'text': '设置', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SettingsPage.value}'})
    if isOwn:
        d.append([])
        i += 1
        d[i].append({'text': 'RSS全局设置', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.GlobalSettingsPage.value}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardWhenRSS2(hashd: str, config: RSSConfig) -> str:
    d = []
    i = 0
    temp = '启用预览' if config.disable_web_page_preview else '禁用预览'
    d.append([])
    d[i].append(
        {'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.DisableWebPagePreview.value}'})
    temp = '隐藏RSS标题' if config.show_RSS_title else '显示RSS标题'
    d[i].append(
        {'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.ShowRSSTitle.value}'})
    d.append([])
    i = i + 1
    temp = '隐藏内容标题' if config.show_Content_title else '显示内容标题'
    d[i].append(
        {'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.ShowContentTitle.value}'})
    temp = '隐藏内容' if config.show_content else '显示内容'
    d[i].append(
        {'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.ShowContent.value}'})
    d.append([])
    i = i + 1
    temp = '禁用发送媒体' if config.send_media else '启用发送媒体'
    d[i].append(
        {'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SendMedia.value}'})
    temp = '禁用单独一行显示链接' if config.display_entry_link else '启用单独一行显示链接'
    d[i].append({'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.DisplayEntryLink.value}'})
    d.append([])
    i += 1
    temp = '禁用发送图片为文件' if config.send_img_as_file else '启用发送图片为文件'
    d[i].append({'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SendImgAsFile.value}'})
    if have_rssbotlib:
        temp = f"{'禁用' if config.send_ugoira_with_origin_pix_fmt else '启用'}发送原始像素格式的Pixiv动图"
        d[i].append({'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SendUgoiraWithOriginPixFmt.value}'})
        d.append([])
        i += 1
        temp2 = SendUgoiraMethod((config.send_ugoira_method.value + 1) % 4)
        temp = f'发送Pixiv动图为{temp2}'
        d[i].append({'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SendUgoiraMethod.value},{temp2.value}'})
        temp = f"{'禁用' if config.compress_big_image else '启用'}压缩过大图片"
        d[i].append({'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.CompressBigImage.value}'})
    d.append([])
    i += 1
    d[i].append({'text': f'{"管理" if config.thread_ids.isEnabled else "启用"}发送到话题功能', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.EnableTopic.value}'})
    d.append([])
    i += 1
    d[i].append(
        {'text': '返回', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.BackToNormalPage.value}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardWhenRSS3(hashd: str, config: RSSConfig):
    d = [[]]
    i = 0
    temp = '禁用发送时使用原文件名' if config.send_origin_file_name else '启用发送时使用原文件名'
    d[i].append({'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SendOriginFileName.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '返回', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.BackToNormalPage.value}'})
    return {'inline_keyboard': d}


def getInlineKeyBoardWhenRSS4(hashd: str, config: RSSConfig) -> str:
    d = [[]]
    i = 0
    d[i].append({'text': '添加新的话题', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.AddTopicToList.value}'})
    if config.thread_ids.isEnabled:
        d.append([])
        i += 1
        temp = f"{'禁用' if config.thread_ids._without_id else '启用'}发送到默认话题"
        d[i].append({'text': temp, 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.EnableSendWithoutTopicId.value}'})
        d.append([])
        i += 1
        d[i].append({'text': '移除已有的话题', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.RemoveTopicFromList.value}'})
        d.append([])
        i += 1
        d[i].append({'text': '禁用发送到话题功能', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.DisableTopic.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '返回', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.SettingsPage.value}'})
    return {'inline_keyboard': d}


class main:
    def __init__(self):
        pass

    def _request(self, methodName: str, HTTPMethod: str = 'get', data: dict = None, json: dict = None, files: dict = None, returnType: str = 'json', telegramBotApiServer: str = None):
        try:
            if json is not None and files is not None:
                data = json2data(json)
                json = None
            r = self._r.request(
                HTTPMethod, f'{self._telegramBotApiServer if telegramBotApiServer is None else telegramBotApiServer}/bot{self._setting.token}/{methodName}', data=data, json=json, files=files)
            if r.status_code not in [200, 400]:
                return None
            if returnType == 'json':
                return r.json()
            elif returnType == 'text':
                return r.text
            elif returnType == 'content':
                return r.content
        except:
            print(format_exc())
            return None

    def _sendMessage(self, chatId: int, meta: dict, content: dict, config: RSSConfig, messageThreadId: Optional[int], returnError: bool = False, testMessage: bool = False):
        with self._tempFileEntries._value_lock:
            return self.__sendMessage(chatId, meta, content, config, messageThreadId, returnError, testMessage)

    def __sendMessage(self, chatId: int, meta: dict, content: dict, config: RSSConfig, messageThreadId: Optional[int], returnError: bool = False, testMessage: bool = False):
        # TODO: 新增文件层面的重试机制
        di = {}
        di['chat_id'] = chatId
        if messageThreadId is not None:
            di['message_thread_id'] = messageThreadId
        text = textc()
        if testMessage:
            text.addtotext('#测试消息')
        if config.show_RSS_title:
            text.addtotext(f"<b>{meta['title']}</b>")
        if config.show_Content_title and 'title' in content and content['title'] is not None and content['title'] != '':
            if 'link' in content and content['link'] is not None and content['link'] != '':
                if not config.display_entry_link:
                    text += f"""<b><a href="{content['link']}">{content['title']}</a></b>"""
                else:
                    text += f"<b>{content['title']}</b>"
                    text += f"""<a href="{content['link']}">{escape(content['link'])}</a>"""
            else:
                text.addtotext(f"<b>{content['title']}</b>")
        elif 'link' in content and content['link'] is not None and content['link'] != '':
            text.addtotext(
                f"""<a href="{content['link']}">{escape(content['link'])}</a>""")
        if config.show_content and 'description' in content and content['description'] is not None and content['description'] != '':
            text.addtotext(removeEmptyLine(content['description']))

        def getListCount(content: dict, key: str):
            if key not in content or content[key] is None:
                return 0
            return len(content[key])
        if not config.send_media or (getListCount(content, 'imgList') == 0 and getListCount(content, 'videoList') == 0 and getListCount(content, 'ugoiraList') == 0):
            if config.disable_web_page_preview:
                di['disable_web_page_preview'] = True
            while len(text) > 0:
                di['text'] = text.tostr()
                di['parse_mode'] = 'HTML'
                for i in range(self._setting.maxRetryCount + 1):
                    re = self._request('sendMessage', 'post', json=di)
                    if re is not None and 'ok' in re and re['ok']:
                        di['reply_to_message_id'] = re['result']['message_id']
                        break
                    if i == self._setting.maxRetryCount:
                        if returnError and re is not None and 'description' in re:
                            return False, re['description']
                        elif returnError:
                            return False, ''
                        else:
                            return False
                    sleep(5)
        elif getListCount(content, 'imgList') == 1 and getListCount(content, 'videoList') == 0 and getListCount(content, 'ugoiraList') == 0:
            f = True
            while len(text) > 0 or f:
                if f:
                    di['caption'] = text.tostr(1024)
                else:
                    di['text'] = text.tostr()
                di['parse_mode'] = 'HTML'
                for i in range(self._setting.maxRetryCount + 1):
                    if f:
                        if not self._setting.downloadMediaFile:
                            di['photo'] = content['imgList'][0]
                            re = self._request('sendPhoto', 'post', json=di)
                        else:
                            fileEntry = self._tempFileEntries.add(
                                content['imgList'][0], config)
                            if not fileEntry.ok:
                                if fileEntry.connect_error:
                                    continue
                                else:
                                    f = False
                                    text.addtotext2(di['caption'])
                                    break
                            should_use_file = False if not config.send_img_as_file else True
                            is_supported_photo = None
                            is_too_big = None
                            compressed_file = None
                            if self._rssbotLib is not None:
                                ttmp = self._rssbotLib.is_supported_photo(fileEntry)
                                if ttmp is not None:
                                    is_supported_photo = ttmp[0]
                                    is_too_big = ttmp[1]
                                if not should_use_file and is_supported_photo is not None:
                                    should_use_file = not is_supported_photo
                                    if is_too_big is True and config.compress_big_image:
                                        compressed_file = self._rssbotLib.compress_image(fileEntry)
                                        if compressed_file is not None:
                                            should_use_file = False
                                elif fileEntry._fileSize >= MAX_PHOTO_SIZE:
                                    should_use_file = True
                            elif fileEntry._fileSize >= MAX_PHOTO_SIZE:
                                should_use_file = True
                            if self._setting.sendFileURLScheme:
                                if not should_use_file:
                                    if compressed_file is None:
                                        di['photo'] = fileEntry._localURI
                                    else:
                                        di['photo'] = compressed_file._localURI
                                    re = self._request('sendPhoto', 'post', json=di)
                                else:
                                    di['document'] = fileEntry._localURI
                                    if is_supported_photo is False or (self._rssbotLib is not None and fileEntry._fileSize >= MAX_PHOTO_SIZE):
                                        if self._rssbotLib.convert_to_tg_thumbnail(fileEntry, 'jpeg'):
                                            thumb_file = fileEntry.getSubFile('_thumbnail', 'jpeg')
                                            di['thumb'] = thumb_file._localURI
                                    re = self._request('sendDocument', 'post', json=di)
                            else:
                                ttmp = fileEntry if compressed_file is None else compressed_file
                                ttmp.open()
                                if not should_use_file:
                                    re = self._request('sendPhoto', 'post', json=di, files={
                                                       'photo': (ttmp._fullfn, ttmp._f)})
                                else:
                                    send_files = {'document': (fileEntry._fullfn, fileEntry._f)}
                                    if is_supported_photo is False or (self._rssbotLib is not None and fileEntry._fileSize >= MAX_PHOTO_SIZE):
                                        if self._rssbotLib.convert_to_tg_thumbnail(fileEntry, 'jpeg'):
                                            thumb_file = fileEntry.getSubFile('_thumbnail', 'jpeg')
                                            thumb_file.open()
                                            send_files['thumb'] = (thumb_file._fullfn, thumb_file._f)
                                    re = self._request('sendDocument', 'post', json=di, files=send_files)
                    else:
                        re = self._request('sendMessage', 'post', json=di)
                    if re is not None and 'ok' in re and re['ok']:
                        di['reply_to_message_id'] = re['result']['message_id']
                        if f:
                            del di['caption']
                            if 'photo' in di:
                                del di['photo']
                            if 'document' in di:
                                del di['document']
                            f = False
                            if config.disable_web_page_preview:
                                di['disable_web_page_preview'] = True
                        break
                    if i == self._setting.maxRetryCount:
                        if returnError and re is not None and 'description' in re:
                            return False, re['description']
                        elif returnError:
                            return False, ''
                        else:
                            return False
                    sleep(5)
        elif getListCount(content, 'imgList') == 0 and getListCount(content, 'videoList') == 1 and getListCount(content, 'ugoiraList') == 0:
            f = True
            while len(text) > 0 or f:
                if f:
                    di['caption'] = text.tostr(1024)
                else:
                    di['text'] = text.tostr()
                di['parse_mode'] = 'HTML'
                for i in range(self._setting.maxRetryCount + 1):
                    if f:
                        if self._setting.downloadMediaFile and not self._setting.sendFileURLScheme:
                            di2 = {}
                        if not self._setting.downloadMediaFile:
                            di['video'] = content['videoList'][0]['src']
                        else:
                            fileEntry = self._tempFileEntries.add(
                                content['videoList'][0]['src'], config)
                            if not fileEntry.ok:
                                if fileEntry.connect_error:
                                    continue
                                else:
                                    break
                            if self._setting.sendFileURLScheme:
                                di['video'] = fileEntry._localURI
                            else:
                                fileEntry.open()
                                di2['video'] = (
                                    fileEntry._fullfn, fileEntry._f)
                        if 'poster' in content['videoList'][0] and content['videoList'][0]['poster'] is not None and content['videoList'][0]['poster'] != '':
                            if not self._setting.downloadMediaFile:
                                di['thumb'] = content['videoList'][0]['poster']
                            else:
                                fileEntry = self._tempFileEntries.add(
                                    content['videoList'][0]['poster'], config)
                                if not fileEntry.ok:
                                    if fileEntry.connect_error:
                                        continue
                                    else:
                                        break
                                if self._setting.sendFileURLScheme:
                                    di['thumb'] = fileEntry._localURI
                                else:
                                    fileEntry.open()
                                    di2['thumb'] = (
                                        fileEntry._fullfn, fileEntry._f)
                        di['supports_streaming'] = True
                        isOk = True
                        if self._rssbotLib is not None:
                            loc = self._tempFileEntries.get(content['videoList'][0]['src'])._abspath if self._setting.downloadMediaFile and self._tempFileEntries.get(
                                content['videoList'][0]['src']) is not None else None
                            addre = self._rssbotLib.addVideoInfo(
                                content['videoList'][0]['src'], di, loc)
                            if addre == AddVideoInfoResult.IsHLS:
                                isOk = False
                                f = False
                                if 'video' in di:
                                    del di['video']
                                if 'thumb' in di:
                                    del di['thumb']
                                del di['supports_streaming']
                                di['text'] = di['caption']
                                del di['caption']
                                if config.disable_web_page_preview:
                                    di['disable_web_page_preview'] = True
                                re = self._request(
                                    'sendMessage', 'post', json=di)
                        if isOk:
                            if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                                re = self._request(
                                    'sendVideo', 'post', json=di)
                            else:
                                re = self._request(
                                    'sendVideo', 'post', json=di, files=di2)
                    else:
                        re = self._request('sendMessage', 'post', json=di)
                    if re is not None and 'ok' in re and re['ok']:
                        di['reply_to_message_id'] = re['result']['message_id']
                        if f:
                            if 'video' in di:
                                del di['video']
                            if 'thumb' in di:
                                del di['thumb']
                            if 'caption' in di:
                                del di['caption']
                            del di['supports_streaming']
                            if 'duration' in di:
                                del di['duration']
                            if 'width' in di:
                                del di['width']
                            if 'height' in di:
                                del di['height']
                            if config.disable_web_page_preview:
                                di['disable_web_page_preview'] = True
                            f = False
                        break
                    if i == self._setting.maxRetryCount:
                        if returnError and re is not None and 'description' in re:
                            return False, re['description']
                        elif returnError:
                            return False, ''
                        else:
                            return False
                    sleep(5)
        elif getListCount(content, 'imgList') == 0 and getListCount(content, 'videoList') == 0 and getListCount(content, 'ugoiraList') == 1:
            f = True
            while len(text) > 0 or f:
                if f:
                    di['caption'] = text.tostr(1024)
                else:
                    di['text'] = text.tostr()
                di['parse_mode'] = 'HTML'
                for i in range(self._setting.maxRetryCount + 1):
                    if f:
                        if self._setting.downloadMediaFile and not self._setting.sendFileURLScheme:
                            di2 = {}
                        if not self._setting.downloadMediaFile:
                            di['photo'] = content['ugoiraList'][0]['poster']
                        else:
                            fileEntry = self._tempFileEntries.add(
                                content['ugoiraList'][0]['poster'], config)
                            if not fileEntry:
                                continue
                            if self._setting.sendFileURLScheme:
                                di['thumb'] = fileEntry._localURI
                            else:
                                fileEntry.open()
                                di2['thumb'] = (
                                    fileEntry._fullfn, fileEntry._f)
                            z = self._tempFileEntries.add(content['ugoiraList'][0]['src'], config)
                            force_yuv420p = not config.send_ugoira_with_origin_pix_fmt
                            if not z.ok and not z.connect_error:
                                break
                            mp4_ok = z.ok and self._rssbotLib is not None and self._rssbotLib.convert_ugoira_to_mp4(z, content['ugoiraList'][0]['frames'], force_yuv420p)
                            if mp4_ok:
                                mp4 = z.getSubFile('_yuv420p' if force_yuv420p else '_origin', 'mp4')
                                if config.send_ugoira_method == SendUgoiraMethod.VIDEO:
                                    send_method = 1
                                elif config.send_ugoira_method == SendUgoiraMethod.FILE:
                                    send_method = 2
                                elif mp4._fileSize >= MAX_ANIMATION_SIZE:
                                    if config.send_ugoira_method == SendUgoiraMethod.ANIMATION_FILE:
                                        send_method = 2
                                    else:
                                        send_method = 1
                                else:
                                    send_method = 0
                                # TODO: Generate a better thumb
                                if self._setting.sendFileURLScheme:
                                    del di['thumb']
                                    if send_method == 0:
                                        di['animation'] = mp4._localURI
                                    elif send_method == 1:
                                        di['video'] = mp4._localURI
                                    elif send_method == 2:
                                        di['document'] = mp4._localURI
                                else:
                                    del di2['thumb']
                                    mp4.open()
                                    if send_method == 0:
                                        di2['animation'] = (mp4._path, mp4._f)
                                    elif send_method == 1:
                                        di2['video'] = (mp4._path, mp4._f)
                                    elif send_method == 2:
                                        di2['document'] = (mp4._path, mp4._f)
                                if send_method < 2:
                                    self._rssbotLib.addVideoInfo(mp4._path, di)
                                if self._setting.sendFileURLScheme:
                                    if send_method == 0:
                                        re = self._request('sendAnimation', 'post', json=di)
                                    elif send_method == 1:
                                        re = self._request('sendVideo', 'post', json=di)
                                    elif send_method == 2:
                                        re = self._request('sendDocument', 'post', json=di)
                                else:
                                    if send_method == 0:
                                        re = self._request('sendAnimation', 'post', json=di, files=di2)
                                    elif send_method == 1:
                                        re = self._request('sendVideo', 'post', json=di, files=di2)
                                    elif send_method == 2:
                                        re = self._request('sendDocument', 'post', json=di, files=di2)
                            else:
                                should_use_file = False if fileEntry._fileSize < MAX_PHOTO_SIZE and not config.send_img_as_file else True
                                if self._setting.sendFileURLScheme:
                                    if not should_use_file:
                                        di['photo'] = di['thumb']
                                        re = self._request('sendPhoto', 'post', json=di)
                                    else:
                                        di['document'] = di['thumb']
                                        re = self._request('sendDocument', 'post', json=di)
                                else:
                                    if not should_use_file:
                                        di2['photo'] = di2['thumb']
                                        re = self._request('sendPhoto', 'post', json=di, files=di2)
                                    else:
                                        di2['document'] = di2['thumb']
                                        re = self._request('sendDocument', 'post', json=di, files=di2)
                    else:
                        re = self._request('sendMessage', 'post', json=di)
                    if re is not None and 'ok' in re and re['ok']:
                        di['reply_to_message_id'] = re['result']['message_id']
                        if f:
                            if 'photo' in di:
                                del di['photo']
                            if 'document' in di:
                                del di['document']
                            if 'animation' in di:
                                del di['animation']
                            if 'video' in di:
                                del di['video']
                            if 'thumb' in di:
                                del di['thumb']
                            if 'caption' in di:
                                del di['caption']
                            if 'duration' in di:
                                del di['duration']
                            if 'width' in di:
                                del di['width']
                            if 'height' in di:
                                del di['height']
                            if config.disable_web_page_preview:
                                di['disable_web_page_preview'] = True
                            f = False
                        break
                    if i == self._setting.maxRetryCount:
                        if returnError and re is not None and 'description' in re:
                            return False, re['description']
                        elif returnError:
                            return False, ''
                        else:
                            return False
                    sleep(5)
        else:
            ind = 0
            if self._setting.downloadMediaFile and not self._setting.sendFileURLScheme:
                ind2 = 0
                di3 = {}
            di['media'] = []
            contain_files = False
            contain_nonfiles = False
            re = None
            def send_file_in_list():
                nonlocal re
                nonlocal di
                nonlocal di3
                if len(di['media']) == 1:
                    tmp_di = di['media'][0]
                    for k in di.keys():
                        if k != 'media':
                            tmp_di[k] = di[k]
                    di['media'] = di['media'][1:]
                    if tmp_di['type'] == 'photo':
                        if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                            tmp_di['photo'] = tmp_di['media']
                        else:
                            tmp_di3 = {}
                            mekey = tmp_di['media'][9:]
                            tmp_di3['photo'] = di3[mekey]
                            del di3[mekey]
                        del tmp_di['media']
                        for _ in range(self._setting.maxRetryCount + 1):
                            if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                                re = self._request('sendPhoto', 'post', json=tmp_di)
                            else:
                                re = self._request(
                                    'sendPhoto', 'post', json=tmp_di, files=tmp_di3)
                            if re is not None and 'ok' in re and re['ok']:
                                di['reply_to_message_id'] = re['result']['message_id']
                                break
                            sleep(5)
                    elif tmp_di['type'] == 'video':
                        if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                            tmp_di['video'] = tmp_di['media']
                        else:
                            tmp_di3 = {}
                            mekey = tmp_di['media'][9:]
                            tmp_di3['video'] = di3[mekey]
                            del di3[mekey]
                            if 'thumb' in tmp_di:
                                mekey = tmp_di['thumb'][9:]
                                tmp_di3['thumb'] = di3[mekey]
                                del di3[mekey]
                        del tmp_di['media']
                        for _ in range(self._setting.maxRetryCount + 1):
                            if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                                re = self._request('sendVideo', 'post', json=tmp_di)
                            else:
                                re = self._request(
                                    'sendVideo', 'post', json=tmp_di, files=tmp_di3)
                            if re is not None and 'ok' in re and re['ok']:
                                di['reply_to_message_id'] = re['result']['message_id']
                                break
                            sleep(5)
                    elif tmp_di['type'] == 'document':
                        if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                            tmp_di['document'] = tmp_di['media']
                        else:
                            tmp_di3 = {}
                            mekey = tmp_di['media'][9:]
                            tmp_di3['document'] = di3[mekey]
                            del di3[mekey]
                            if 'thumb' in tmp_di:
                                mekey = tmp_di['thumb'][9:]
                                tmp_di3['thumb'] = di3[mekey]
                                del di3[mekey]
                        del tmp_di['media']
                        for _ in range(self._setting.maxRetryCount + 1):
                            if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                                re = self._request('sendDocument', 'post', json=tmp_di)
                            else:
                                re = self._request(
                                    'sendDocument', 'post', json=tmp_di, files=tmp_di3)
                            if re is not None and 'ok' in re and re['ok']:
                                di['reply_to_message_id'] = re['result']['message_id']
                                break
                            sleep(5)
                    elif tmp_di['type'] == 'animation':
                        if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                            tmp_di['animation'] = tmp_di['media']
                        else:
                            tmp_di3 = {}
                            mekey = tmp_di['media'][9:]
                            tmp_di3['animation'] = di3[mekey]
                            del di3[mekey]
                            if 'thumb' in tmp_di:
                                mekey = tmp_di['thumb'][9:]
                                tmp_di3['thumb'] = di3[mekey]
                                del di3[mekey]
                        del tmp_di['media']
                        for _ in range(self._setting.maxRetryCount + 1):
                            if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                                re = self._request('sendAnimation', 'post', json=tmp_di)
                            else:
                                re = self._request(
                                    'sendAnimation', 'post', json=tmp_di, files=tmp_di3)
                            if re is not None and 'ok' in re and re['ok']:
                                di['reply_to_message_id'] = re['result']['message_id']
                                break
                            sleep(5)
                else:
                    for _ in range(self._setting.maxRetryCount + 1):
                        if not self._setting.downloadMediaFile or self._setting.sendFileURLScheme:
                            re = self._request('sendMediaGroup', 'post', json=di)
                            if re is not None and 'ok' in re and re['ok']:
                                di['reply_to_message_id'] = re['result'][0]['message_id']
                                di['media'] = []
                                break
                        else:
                            re = self._request(
                                'sendMediaGroup', 'post', json=di, files=di3)
                            if re is not None and 'ok' in re and re['ok']:
                                di['reply_to_message_id'] = re['result'][0]['message_id']
                                di['media'] = []
                                di3 = {}
                                break
                        sleep(5)
                nonlocal contain_files
                nonlocal contain_nonfiles
                contain_files = False
                contain_nonfiles = False

            for i in content['imgList']:
                if len(di['media']) == MAX_ITEM_IN_MEDIA_GROUP:
                    send_file_in_list()
                di2 = {'type': 'photo'}
                if not self._setting.downloadMediaFile:
                    di2['media'] = i
                    if contain_files:
                        send_file_in_list()
                    contain_nonfiles = True
                else:
                    fileEntry = self._tempFileEntries.add(i, config)
                    if not fileEntry.ok:
                        if fileEntry.connect_error:
                            continue
                        else:
                            break
                    should_use_file = False if not config.send_img_as_file else True
                    is_supported_photo = None
                    is_too_big = None
                    compressed_file = None
                    if self._rssbotLib is not None:
                        ttmp = self._rssbotLib.is_supported_photo(fileEntry)
                        if ttmp is not None:
                            is_supported_photo = ttmp[0]
                            is_too_big = ttmp[1]
                        if not should_use_file and is_supported_photo is not None:
                            should_use_file = not is_supported_photo
                            if is_too_big is True and config.compress_big_image:
                                compressed_file = self._rssbotLib.compress_image(fileEntry)
                                if compressed_file is not None:
                                    should_use_file = False
                        elif fileEntry._fileSize >= MAX_PHOTO_SIZE:
                            should_use_file = True
                    elif fileEntry._fileSize >= MAX_PHOTO_SIZE:
                        should_use_file = True
                    if should_use_file:
                        if contain_nonfiles:
                            send_file_in_list()
                        contain_files = True
                        di2['type'] = 'document'
                        if is_supported_photo is False or (self._rssbotLib is not None and fileEntry._fileSize >= MAX_PHOTO_SIZE):
                            if self._rssbotLib.convert_to_tg_thumbnail(fileEntry, 'jpeg'):
                                thumb_file = fileEntry.getSubFile('_thumbnail', 'jpeg')
                                if self._setting.sendFileURLScheme:
                                    di2['thumb'] = thumb_file._localURI
                                else:
                                    thumb_file.open()
                                    di2['thumb'] = f'attach://file{ind2}'
                                    di3[f'file{ind2}'] = (thumb_file._fullfn, fileEntry._f)
                                    ind2 += 1
                    else:
                        if contain_files:
                            send_file_in_list()
                        contain_nonfiles = True
                    if self._setting.sendFileURLScheme:
                        if compressed_file is None:
                            di2['media'] = fileEntry._localURI
                        else:
                            di2['media'] = compressed_file._localURI
                    else:
                        ttmp = fileEntry if compressed_file is None else compressed_file
                        ttmp.open()
                        di2['media'] = f'attach://file{ind2}'
                        di3[f'file{ind2}'] = (ttmp._fullfn, ttmp._f)
                        ind2 = ind2 + 1
                if len(di['media']) == 0:
                    di2['caption'] = text.tostr(1024)
                    di2['parse_mode'] = 'HTML'
                di['media'].append(di2)
                ind = ind + 1
            for i in content['videoList']:
                if len(di['media']) == MAX_ITEM_IN_MEDIA_GROUP:
                    send_file_in_list()
                di2 = {'type': 'video', 'supports_streaming': True}
                if not self._setting.downloadMediaFile:
                    di2['media'] = i['src']
                else:
                    fileEntry = self._tempFileEntries.add(i['src'], config)
                    if not fileEntry.ok:
                        if fileEntry.connect_error:
                            continue
                        else:
                            break
                    if self._setting.sendFileURLScheme:
                        di2['media'] = fileEntry._localURI
                    else:
                        fileEntry.open()
                        di2['media'] = f'attach://file{ind2}'
                        di3[f'file{ind2}'] = (fileEntry._fullfn, fileEntry._f)
                        ind2 = ind2 + 1
                if contain_files:
                    send_file_in_list()
                contain_nonfiles = True
                if 'poster' in i and i['poster'] is not None and i['poster'] != '':
                    if not self._setting.downloadMediaFile:
                        di2['thumb'] = i['poster']
                    else:
                        fileEntry = self._tempFileEntries.add(i['poster'], config)
                        if not fileEntry.ok:
                            if fileEntry.connect_error:
                                continue
                            else:
                                break
                        if self._setting.sendFileURLScheme:
                            di2['thumb'] = fileEntry._localURI
                        else:
                            fileEntry.open()
                            di2['thumb'] = f'attach://file{ind2}'
                            di3[f'file{ind2}'] = (
                                fileEntry._fullfn, fileEntry._f)
                            ind2 = ind2 + 1
                if len(di['media']) == 0:
                    di2['caption'] = text.tostr(1024)
                    di2['parse_mode'] = 'HTML'
                if self._rssbotLib is not None:
                    loc = self._tempFileEntries.get(i['src'])._abspath if self._setting.downloadMediaFile and self._tempFileEntries.get(
                        i['src']) is not None else None
                    addre = self._rssbotLib.addVideoInfo(i['src'], di2, loc)
                    if addre == AddVideoInfoResult.IsHLS:
                        continue
                di['media'].append(di2)
                ind = ind + 1
            if len(di['media']) > 0:
                send_file_in_list()
            if len(text) > 0:
                di = {}
                di['chat_id'] = chatId
                if messageThreadId is not None:
                    di['message_thread_id'] = messageThreadId
                if config.disable_web_page_preview:
                    di['disable_web_page_preview'] = True
                if re is not None and 'ok' in re and re['ok']:
                    if isinstance(re['result'], list):
                        di['reply_to_message_id'] = re['result'][0]['message_id']
                    else:
                        di['reply_to_message_id'] = re['result']['message_id']
            while len(text) > 0:
                di['text'] = text.tostr()
                di['parse_mode'] = 'HTML'
                for i in range(self._setting.maxRetryCount + 1):
                    re = self._request('sendMessage', 'post', json=di)
                    if re is not None and 'ok' in re and re['ok']:
                        di['reply_to_message_id'] = re['result']['message_id']
                        break
                    if i == self._setting.maxRetryCount:
                        if returnError and re is not None and 'description' in re:
                            return False, re['description']
                        elif returnError:
                            return False, ''
                        else:
                            return False
                    sleep(5)
        if re is not None and 'ok' in re and re['ok']:
            if returnError:
                return True, ''
            return True
        if returnError and re is not None and 'description' in re:
            return False, re['description']
        elif returnError:
            return False, ''
        return False

    def getChatName(self, chatId: int) -> str:
        name = self._db.getChatName(chatId)
        if name is not None:
            return name
        re = self._request('getChat', 'post', {'chat_id': chatId})
        if re is not None and 'ok' in re and re['ok']:
            name = None
            re = re['result']
            type = re['type']
            if type == 'private':
                name = re['first_name']
                if 'last_name' in re:
                    name = name + ' ' + re['last_name']
                if 'username' in re:
                    name = name + '(@' + re['username'] + ')'
            else:
                name = re['title']
                if 'username' in re:
                    name = name + '(@' + re['username'] + ')'
            if name is not None:
                self._db.saveChatName(chatId, name)
            else:
                name = str(chatId)
            return name
        else:
            print(re)
            return str(chatId)

    def _updateLoop(self):
        d = {'allowed_updates': ['message', 'edited_message',
                                 'channel_post', 'edited_channel_post', 'callback_query']}
        if self._upi is not None:
            d['offset'] = self._upi
        ud = self._request('getUpdates', 'post', json=d)
        if ud is not None and 'ok' in ud and ud['ok']:
            for i in ud['result']:
                for key in ['message', 'edited_message', 'channel_post', 'edited_channel_post']:
                    if key in i:
                        m = messageHandle(self, i[key])
                        m.start()
                if 'callback_query' in i:
                    m = callbackQueryHandle(self, i['callback_query'])
                    m.start()
                self._upi = i['update_id'] + 1

    def checkChatIsForum(self, chatId: int):
        re = self._request('getChat', data={'chat_id': chatId})
        if re is None or 'ok' not in re or not re['ok']:
            return '获取Chat信息失败'
        re = re['result']
        return 'is_forum' in re and re['is_forum'] is True
        

    def start(self):
        self._commandLine = commandline()
        if len(sys.argv) > 1:
            self._commandLine.parse(sys.argv[1:])
        if self._commandLine.remoteDebug:
            import debugpy
            debugpy.listen(('0.0.0.0', 4500))
            print("Waiting for debugger attach")
            debugpy.wait_for_client()
        if not exists('settings.txt'):
            print('找不到settings.txt')
            return -1
        self._setting = settings(self, self._commandLine._config)
        if self._setting.token is None:
            print('没有机器人token')
            return -1
        self._telegramBotApiServer = self._setting.telegramBotApiServer
        self._db = database(self, self._setting.databaseLocation)
        if self._setting.miraiApiHTTPServer is not None:
            if self._setting.miraiApiHTTPAuthKey is None:
                print('未设置AuthKey。')
                return -1
            if self._setting.miraiApiQQ is None:
                print('未设置QQ号。')
                return -1
            self._mriaidb = MiraiDatabase(self, self._setting.databaseLocation)
            self._mriai = Mirai(self)
        self._r = Session()
        if self._telegramBotApiServer != 'https://api.telegram.org':
            self._request("logOut", "post",
                          telegramBotApiServer="https://api.telegram.org")
        remove('Temp')
        self._tempFileEntries = FileEntries(self)
        self._me = self._request('getMe')
        self._rssMetaList = rssMetaList()
        print(self._me)
        if self._me is None or 'ok' not in self._me or not self._me['ok']:
            print('无法读取机器人信息')
        self._me = self._me['result']
        self._rssbotLib = loadRSSBotLib(self)
        self._blackList = BlackList(self)
        self._blackList.checkRSSList()
        self._upi = None
        self._updateThread = updateThread(self)
        self._updateThread.start()
        self._rssCheckerThread = RSSCheckerThread(self)
        self._rssCheckerThread.start()


class updateThread(Thread):
    def __init__(self, main: main):
        Thread.__init__(self)
        self._main = main

    def run(self):
        t = None
        while True:
            if t is not None and time() - t < 0.1:
                sleep(0.1)
            t = time()
            self._main._updateLoop()


class messageHandle(Thread):
    def __init__(self, main: main, data: dict):
        Thread.__init__(self)
        self._main = main
        self._data = data

    def __getBotCommand(self) -> str:
        for i in self._data['entities']:
            if i['type'] == 'bot_command':
                v = self._data['text'][i['offset']: i['offset'] + i['length']]
                founded = v.find('@')
                if founded == -1:
                    return v
                return v[0:founded]
        return None

    def __getChatId(self) -> int:
        if 'chat' in self._data:
            return self._data['chat']['id']
        return None

    def __getChatType(self) -> str:
        if 'chat' in self._data:
            return self._data['chat']['type']
        return None

    def __getFromUserId(self) -> int:
        if 'from' in self._data:
            return self._data['from']['id']
        return None

    def _getCommandlinePara(self) -> List[str]:
        s = self._data['text']
        if 'entities' in self._data:
            for i in self._data['entities']:
                if i['type'] == 'bot_command':
                    s = s[:i['offset']] + s[i['offset']+i['length']:]
                    break
        l = s.split(' ')
        r = []
        t = ''
        quote = False
        for i in l:
            if i != '':
                if quote:
                    if i[-1] == '"':
                        quote = False
                        t = t + ' ' + i[:-1]
                        r.append(t)
                        t = ''
                    else:
                        t = t + ' ' + i
                else:
                    if i[0] == '"':
                        if i[-1] == '"':
                            r.append(i[1:-1])
                        else:
                            quote = True
                            t = i[1:]
                    else:
                        r.append(i)
        if t != '':
            r.append(t)
        return r

    def run(self):
        print(self._data)
        for key in ["new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo", "pinned_message"]:
            if key in self._data:
                return
        if self._data['chat']['type'] == 'channel':
            return
        self._messageId = self._data['message_id']
        self._chatId = self.__getChatId()
        self._messageThreadId = self._data['message_thread_id'] if 'message_thread_id' in self._data else None
        if self._chatId is None:
            print('未知的chat id')
            return -1
        self._fromUserId = self.__getFromUserId()
        self._isOwn = self._main._setting.botOwnerList.isOwner(self._fromUserId)
        if self._main._blackList.isInBlackList(self._chatId) and not self._isOwn:
            c = self.__getChatType()
            if c == 'private':
                c = '您'
            elif c in ['supergroup', 'group']:
                c = '该群组'
            elif c == 'channel':
                c = '该频道'
            di = {'chat_id': self._chatId, 'text': f'{c}已被封禁。'}
            self._main._request("sendMessage", 'post', json=di)
            return
        self._botCommand = None
        if 'text' in self._data:
            if 'entities' in self._data:
                self._botCommand = self.__getBotCommand()
        if self._fromUserId is not None:
            di = {'chat_id': self._chatId}
            if self.__getChatType() in ['supergroup', 'group'] and self._fromUserId is not None:
                di['reply_to_message_id'] = self._messageId
            if self._main._blackList.isInBlackList(self._fromUserId):
                di['text'] = '您已被封禁。'
                self._main._request("sendMessage", 'post', json=di)
                return
            self._userStatus, self._hashd = self._main._db.getUserStatus(
                self._fromUserId)
            if self._userStatus == userStatus.normalStatus:
                pass
            elif self._botCommand is not None and self._botCommand == '/cancle':
                if self._userStatus == userStatus.needInputChatId:
                    di['text'] = '已取消输入群/频道ID。'
                elif self._userStatus == userStatus.needInputThreadId:
                    di['text'] = '已取消新增话题ID。'
                elif self._userStatus == userStatus.needRemoveThreadId:
                    di['text'] = '已取消移除话题ID。'
                self._main._db.setUserStatus(
                    self._fromUserId, userStatus.normalStatus)
                self._main._request('sendMessage', 'post', json=di)
                return
            elif self._botCommand == '/this' and self._userStatus in [userStatus.needInputThreadId, userStatus.needRemoveThreadId] and self._messageThreadId is not None:
                hashd = self._hashd.split(',')
                if hashd[0] == '0':
                    metainfo = self._main._rssMetaList.getRSSMeta(hashd[1])
                    if metainfo is None:
                        self._main._db.setUserStatus(
                            self._fromUserId, userStatus.normalStatus)
                        di['text'] = '已过期。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    if metainfo.chatId != self._chatId:
                        di['text'] = 'Chat ID不一致，请在同一个群里回复机器人。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    if self._userStatus == userStatus.needInputThreadId:
                        metainfo.config.thread_ids.addId(self._messageThreadId)
                        di['text'] = '添加成功。'
                    else:
                        if not metainfo.config.thread_ids.removeId(self._messageThreadId):
                            di['text'] = '移除失败。该话题不在列表中。'
                            self._main._request('sendMessage', 'post', json=di)
                            return
                        else:
                            di['text'] = '移除成功。'
                    self._main._request('sendMessage', 'post', json=di)
                    di2 = {'chat_id': metainfo.chatId, 'message_id': metainfo.messageId}
                    di2['text'] = getMediaInfo(metainfo.meta, metainfo.config)
                    di2['parse_mode'] = 'HTML'
                    di2['disable_web_page_preview'] = True
                    di2['reply_markup'] = getInlineKeyBoardWhenRSS4(
                        hashd[1], metainfo.config)
                    self._main._request("editMessageText", "post", json=di2)
                    self._main._db.setUserStatus(
                        self._fromUserId, userStatus.normalStatus)
                    return
                elif hashd[0] == '1':
                    chatId = int(hashd[1])
                    messageId = int(hashd[2])
                    ind = int(hashd[3])
                    rssId = int(hashd[4])
                    rssEntry = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                    if rssEntry is None:
                        self._main._db.setUserStatus(
                            self._fromUserId, userStatus.normalStatus)
                        di['text'] = '找不到RSS。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    chatEntry: ChatEntry = rssEntry.chatList[0]
                    if chatId != self._chatId:
                        di['text'] = 'Chat ID不一致，请在同一个群里回复机器人。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    if self._userStatus == userStatus.needInputThreadId:
                        chatEntry.config.thread_ids.addId(self._messageThreadId)
                        di['text'] = '添加成功。'
                    else:
                        if not chatEntry.config.thread_ids.removeId(self._messageThreadId):
                            di['text'] = '移除失败。该话题不在列表中。'
                            self._main._request('sendMessage', 'post', json=di)
                            return
                        else:
                            di['text'] = '移除成功。'
                    if not self._main._db.updateChatConfig(chatEntry):
                        di['text'] = '将更改更新到数据库失败。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    self._main._request('sendMessage', 'post', json=di)
                    di2 = {'chat_id': chatId, 'message_id': messageId}
                    di2['text'] = getTextContentForRSSInList(rssEntry, self._main._setting)
                    di2['parse_mode'] = 'HTML'
                    di2['reply_markup'] = getInlineKeyBoardForRSSThreadIdsInList(
                        chatId, rssEntry, ind)
                    self._main._request("editMessageText", "post", json=di2)
                    self._main._db.setUserStatus(
                        self._fromUserId, userStatus.normalStatus)
                    return
            elif self._userStatus in [userStatus.needInputChatId]:
                metainfo = self._main._rssMetaList.getRSSMeta(self._hashd)
                if metainfo is None:
                    self._main._db.setUserStatus(
                        self._fromUserId, userStatus.normalStatus)
                    di['text'] = '已过期。'
                    self._main._request('sendMessage', 'post', json=di)
                    return
                elif self._userStatus == userStatus.needInputChatId:
                    para = self._getCommandlinePara()
                    chatId = None
                    for i in para:
                        if search(r'^[\+-]?[0-9]+$', i) is not None:
                            chatId = int(i)
                            break
                    if chatId is None:
                        di['text'] = '找不到ID。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    di['text'] = '正在获取群/频道信息……'
                    re = self._main._request('sendMessage', 'post', json=di)
                    if re is not None and 'ok' in re and re['ok']:
                        re = re['result']
                        di = {'chat_id': self._chatId,
                              'message_id': re['message_id']}
                        re2 = self._main._request(
                            'getChat', 'post', {'chat_id': chatId})
                        if re2 is not None and 'ok' in re2 and re2['ok']:
                            re2 = re2['result']
                            if re2['type'] == "private":
                                di['text'] = '该ID是私聊。'
                                self._main._request(
                                    'editMessageText', 'post', json=di)
                                return
                            di['text'] = '正在获取群/频道管理员列表……'
                            self._main._request(
                                'editMessageText', 'post', json=di)
                            re3 = self._main._request(
                                'getChatAdministrators', 'post', {'chat_id': chatId})
                            if re3 is not None and 'ok' in re3 and re3['ok']:
                                re3 = re3['result']
                                chatM = None
                                for chatMember in re3:
                                    if chatMember['user']['id'] != self._fromUserId:
                                        continue
                                    if chatMember['status'] not in ['creator', 'administrator']:
                                        continue
                                    if re2['type'] == 'channel' and chatMember['status'] == 'administrator' and ('can_post_messages' not in chatMember or not chatMember['can_post_messages']):
                                        continue
                                    chatM = chatMember
                                if chatM is None:
                                    di['text'] = '你没有权限操作。'
                                    self._main._request(
                                        'editMessageText', 'post', json=di)
                                    return
                                di['text'] = '正在确认机器人的权限……'
                                self._main._request(
                                    'editMessageText', 'post', json=di)
                                re4 = self._main._request("getChatMember", "post", {
                                                          "chat_id": chatId, "user_id": self._main._me['id']})
                                if re4 is not None and 'ok' in re4 and re4['ok']:
                                    re4 = re4['result']
                                    if re2['type'] == 'channel' and (re4['status'] not in ['creator', 'administrator'] or not re4['can_post_messages']):
                                        di['text'] = '机器人在频道内缺少必要的权限'
                                        self._main._request(
                                            'editMessageText', 'post', json=di)
                                        return
                                    if re2['type'] in ["group", "supergroup"]:
                                        if re4['status'] in ['creator', 'administrator']:
                                            pass
                                        elif 'permissions' in re2 and re2['permissions'] is not None and (not re2['permissions']['can_send_messages'] or not re2['permissions']['can_send_media_messages'] or not re2['permissions']['can_send_other_messages'] or not re2['permissions']['can_add_web_page_previews']):
                                            di['text'] = '机器人在群组内缺少必要的权限'
                                            self._main._request(
                                                'editMessageText', 'post', json=di)
                                            return
                                        elif re4['status'] in ['left', 'kicked']:
                                            di['text'] = '机器人不在群组内' if re4['status'] == 'lefy' else '机器人已被踢'
                                            self._main._request(
                                                'editMessageText', 'post', json=di)
                                            return
                                        elif re4['status'] == 'restricted' and (not re4['can_send_messages'] or not re4['can_send_media_messages'] or not re4['can_send_other_messages'] or not re4['can_add_web_page_previews']):
                                            di['text'] = '机器人在群组内缺少必要的权限'
                                            self._main._request(
                                                'editMessageText', 'post', json=di)
                                            return
                                else:
                                    di['text'] = '获取机器人权限失败！'
                                    self._main._request(
                                        'editMessageText', 'post', json=di)
                                    return
                        else:
                            di['text'] = '获取群/频道信息失败！'
                            self._main._request(
                                'editMessageText', 'post', json=di)
                            return
                        metainfo.meta['chatId'] = chatId
                        metainfo.flushTime()
                        di['text'] = '修改完成！'
                        self._main._request('editMessageText', 'post', json=di)
                        di = {'chat_id': metainfo.chatId,
                              'message_id': metainfo.messageId}
                        di['text'] = getMediaInfo(
                            metainfo.meta, metainfo.config)
                        di['parse_mode'] = 'HTML'
                        di['disable_web_page_preview'] = True
                        di['reply_markup'] = getInlineKeyBoardWhenRSS(
                            self._hashd, metainfo.meta, self._isOwn)
                        self._main._request('editMessageText', 'post', json=di)
                        self._main._db.setUserStatus(
                            self._fromUserId, userStatus.normalStatus)
                    return
            elif self._userStatus in [userStatus.needRemoveThreadId]:
                hashd = self._hashd.split(',')
                if hashd[0] == '0':
                    metainfo = self._main._rssMetaList.getRSSMeta(hashd[1])
                    if metainfo is None:
                        self._main._db.setUserStatus(
                            self._fromUserId, userStatus.normalStatus)
                        di['text'] = '已过期。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    para = self._getCommandlinePara()
                    messageThreadId = None
                    for i in para:
                        if search(r'^[\+-]?[0-9]+$', i) is not None:
                            messageThreadId = int(i)
                            break
                    if messageThreadId is None:
                        di['text'] = '找不到话题ID。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    if not metainfo.config.thread_ids.removeId(messageThreadId):
                        di['text'] = '移除失败。该话题不在列表中。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    else:
                        di['text'] = '移除成功。'
                    self._main._request('sendMessage', 'post', json=di)
                    di2 = {'chat_id': metainfo.chatId, 'message_id': metainfo.messageId}
                    di2['text'] = getMediaInfo(metainfo.meta, metainfo.config)
                    di2['parse_mode'] = 'HTML'
                    di2['disable_web_page_preview'] = True
                    di2['reply_markup'] = getInlineKeyBoardWhenRSS4(
                        hashd[1], metainfo.config)
                    self._main._request("editMessageText", "post", json=di2)
                    self._main._db.setUserStatus(
                        self._fromUserId, userStatus.normalStatus)
                    return
                elif hashd[0] == '1':
                    chatId = int(hashd[1])
                    messageId = int(hashd[2])
                    ind = int(hashd[3])
                    rssId = int(hashd[4])
                    rssEntry = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                    if rssEntry is None:
                        self._main._db.setUserStatus(
                            self._fromUserId, userStatus.normalStatus)
                        di['text'] = '找不到RSS。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    chatEntry: ChatEntry = rssEntry.chatList[0]
                    if not chatEntry.config.thread_ids.removeId(ind):
                        di['text'] = '移除失败。该话题不在列表中。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    else:
                        di['text'] = '移除成功。'
                    if not self._main._db.updateChatConfig(chatEntry):
                        di['text'] = '将更改更新到数据库失败。'
                        self._main._request('sendMessage', 'post', json=di)
                        return
                    self._main._request('sendMessage', 'post', json=di)
                    di2 = {'chat_id': chatId, 'message_id': messageId}
                    di2['text'] = getTextContentForRSSInList(rssEntry, self._main._setting)
                    di2['parse_mode'] = 'HTML'
                    di2['reply_markup'] = getInlineKeyBoardForRSSThreadIdsInList(
                        chatId, rssEntry, ind)
                    self._main._request("editMessageText", "post", json=di2)
                    self._main._db.setUserStatus(
                        self._fromUserId, userStatus.normalStatus)
                    return
        if self._botCommand is None and self._data['chat']['type'] in ['group', 'supergroup']:
            return
        if self._botCommand is None or self._botCommand not in ['/help', '/rss', '/rsslist', '/ban', '/banlist', '/unban', '/status', '/manage']:
            self._botCommand = '/help'
        di = {'chat_id': self._chatId}
        if self.__getChatType() in ['supergroup', 'group'] and self._fromUserId is not None:
            di['reply_to_message_id'] = self._messageId
        if self._botCommand == '/help':
            di['text'] = '''/help   显示帮助
/rss url    订阅RSS
/rsslist [chatId]   获取RSS订阅列表
/ban        封禁某用户
/banlist    查询被封禁列表
/unban      取消封禁某用户
/status     返回Bot状态
/manage     管理所有RSS订阅'''
        elif self._botCommand == '/rss':
            self._botCommandPara = self._getCommandlinePara()
            self._uri = None
            for i in self._botCommandPara:
                if i.find('://') > -1:
                    self._uri = decodeURI(i)
                    break
            if self._data['chat']['type'] != "private" and checkUserPermissionsInChat(self._main, self._data['chat']['id'], self._fromUserId) != UserPermissionsInChatCheckResult.OK:
                di['text'] = '你没有权限操作。'
                self._uri = None
            elif self._uri is None:
                di['text'] = '没有找到URL'
            else:
                di['text'] = '正在获取信息中……'
        elif self._botCommand == '/rsslist':
            self._needCheckUser = False
            self._botCommandPara = self._getCommandlinePara()
            targetChatId = self._chatId
            for i in self._botCommandPara:
                if search(r'^[\+-]?[0-9]+$', i) is not None:
                    targetChatId = int(i)
            if targetChatId == self._chatId and self._data['chat']['type'] == 'private':
                try:
                    rssList = self._main._db.getRSSListByChatId(self._chatId)
                    di['text'] = '列表如下：'
                    di['reply_markup'] = getInlineKeyBoardForRSSList(
                        self._chatId, rssList)
                except:
                    di['text'] = '获取列表失败。'
            else:
                di['text'] = '正在确认操作者权限……'
                self._needCheckUser = True
        elif self._botCommand == '/banlist':
            if self._fromUserId is None or not self._main._setting.botOwnerList.isOwner(self._fromUserId):
                di['text'] = '❌你没有权限操作，请与Bot主人进行PY交易以获得权限。'
            else:
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForBlackList(self._main._blackList.getBlackList())
        elif self._botCommand in ['/ban', '/unban']:
            isban = self._botCommand == '/ban'
            words = '封禁' if isban else '取消封禁'
            if self._fromUserId is None or not self._main._setting.botOwnerList.isOwner(self._fromUserId):
                di['text'] = '❌你没有权限操作，请与Bot主人进行PY交易以获得权限。'
            else:
                ban_uid: int = None
                title: str = None
                if 'reply_to_message' in self._data and self._data['reply_to_message'] is not None:
                    try:
                        ban_uid = self._data['reply_to_message']['from']['id']
                        if self._data['reply_to_message']['from']['is_bot']:
                            di['text'] = f'尝试{words}Bot，你的请求被滥权了。'
                            self._main._request('sendMessage', 'post', json=di)
                            return
                        title = self._data['reply_to_message']['from']['first_name']
                        if self._data['reply_to_message']['from']['last_name'] is not None:
                            title += f" {self._data['reply_to_message']['from']['last_name']}"
                        if self._data['reply_to_message']['from']['username'] is not None:
                            title += f" ({self._data['reply_to_message']['from']['username']})"
                    except Exception:
                        pass
                self._botCommandPara = self._getCommandlinePara()
                first_uid = False
                if ban_uid is None:
                    first_uid = True
                    if self._botCommandPara[0] in ['chat', 'channel', 'group']:
                        try:
                            ban_uid = self._data['chat']['id']
                            title = self._data['chat']['title']
                        except Exception:
                            pass
                    else:
                        try:
                            ban_uid = int(self._botCommandPara[0])
                        except Exception:
                            pass
                if ban_uid is None:
                    di['text'] = f'未找到要{words}的用户。'
                elif self._main._setting.botOwnerList.isOwner(ban_uid):
                    di['text'] = f'尝试{words}Bot主人，你的请求被滥权了。'
                else:
                    bl = self._main._blackList.getBlackList()
                    ind = bl.find(ban_uid)
                    if ind > -1:
                        if isban:
                            di['text'] = '该用户已被封禁。'
                            self._main._request('sendMessage', 'post', json=di)
                            return
                        if bl[ind].from_config:
                            di['text'] = '无法取消封禁来自配置文件的用户，请修改配置文件后重启bot。'
                            self._main._request('sendMessage', 'post', json=di)
                            return
                        re = self._main._blackList.unban(bl[ind].uid)
                        if title is None or title == '':
                            title = str(ban_uid)
                        link = '' if ban_uid < 0 else f'tg://user?id={ban_uid}'
                        if re:
                            di['text'] = f'取消封禁<a href="{link}">{title}</a>成功！'
                        else:
                            di['text'] = f'取消封禁<a href="{link}">{title}</a>失败！'
                        di['parse_mode'] = 'HTML'
                    else:
                        if not isban:
                            di['text'] = '该用户未被封禁'
                            self._main._request('sendMessage', 'post', json=di)
                            return
                        reason = ''
                        if first_uid and len(self._botCommandPara) > 1:
                            reason = self._botCommandPara[1]
                        elif not first_uid and len(self._botCommandPara) > 0:
                            reason = self._botCommandPara[0]
                        info = BlackInfo(ban_uid, self._fromUserId, int(time()), reason, title)
                        re = self._main._blackList.ban(info)
                        if title is None or title == '':
                            title = str(ban_uid)
                        link = '' if ban_uid < 0 else f'tg://user?id={ban_uid}'
                        if re:
                            di['text'] = f'封禁<a href="{link}">{title}</a>成功！封禁理由：{reason}'
                        else:
                            di['text'] = f'封禁<a href="{link}">{title}</a>失败！'
                        di['parse_mode'] = 'HTML'
        elif self._botCommand == '/status':
            if self._fromUserId is None or not self._main._setting.botOwnerList.isOwner(self._fromUserId):
                di['text'] = '❌你没有权限操作，请与Bot主人进行PY交易以获得权限。'
            else:
                di['text'] = f'''Bot状态：
RSSBotLib版本: {('<code>' + '.'.join(str(i) for i in self._main._rssbotLib._version) + '</code>') if self._main._rssbotLib is not None else '未发现RSSBotLib'}
数据库版本: <code>{'.'.join(str(i) for i in self._main._db._version)}</code>
RSS地址总数: <code>{self._main._db.getRSSCount()}</code>
RSS订阅总数: <code>{self._main._db.getChatRSSCount()}</code>
用户(含频道、群组)数: <code>{self._main._db.getChatCount()}</code>
内容散列个数: <code>{self._main._db.getHashCount()}</code>
黑名单(不含配置文件)总数: <code>{self._main._db.getUserBlackListCount()}</code>'''
                di['parse_mode'] = 'HTML'
        elif self._botCommand == '/manage':
            if self._fromUserId is None or not self._main._setting.botOwnerList.isOwner(self._fromUserId):
                di['text'] = '❌你没有权限操作，请与Bot主人进行PY交易以获得权限。'
            else:
                di['text'] = '请选择管理模式：'
                di['reply_markup'] = getInlineKeyBoardForManage()
        re = self._main._request('sendMessage', 'post', json=di)
        if self._botCommand == '/rss' and self._uri is not None and re is not None and 'ok' in re and re['ok']:
            re = re['result']
            chatId = re['chat']['id']
            messageId = re['message_id']
            di = {'chat_id': chatId, 'message_id': messageId}
            checked = False
            try:
                p = RSSParser()
                p.parse(self._uri, self._main._setting.RSSTimeout)
                checked = p.check()
            except:
                pass
            if not checked:
                di['text'] = '获取信息失败！'
            else:
                media = p.m
                media['url'] = self._uri
                media['ttl'] = p.ttl
                media['userId'] = None
                if self._fromUserId:
                    media['userId'] = self._fromUserId
                if self._data['chat']['type'] != "private" and checkUserPermissionsInChat(self._main, chatId, self._fromUserId) == UserPermissionsInChatCheckResult.OK:
                    media['chatId'] = chatId
                self._hash = md5WithBase64(
                    f'{self._uri},{self._messageId},{self._chatId}')
                di['text'] = getMediaInfo(media)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS(
                    self._hash, media, self._isOwn)
                try:
                    conf = RSSConfig(loads(self._main._db.getRSSSettingsByUrl(self._uri)))
                except Exception:
                    conf = None
                self._main._rssMetaList.addRSSMeta(rssMetaInfo(
                    re['message_id'], chatId, media, p.itemList, self._hash, conf))
            self._main._request('editMessageText', 'post', json=di)
        if self._botCommand == '/rsslist' and self._needCheckUser and re is not None and 'ok' in re and re['ok']:
            messageInfo = re['result']
            messageChatId = messageInfo['chat']['id']
            messageId = messageInfo['message_id']
            checkResult = checkUserPermissionsInChat(
                self._main, targetChatId, self._fromUserId)
            di = {'chat_id': messageChatId, 'message_id': messageId}
            if checkResult == UserPermissionsInChatCheckResult.OK:
                rssList = self._main._db.getRSSListByChatId(targetChatId)
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForRSSList(
                    targetChatId, rssList)
            elif checkResult == UserPermissionsInChatCheckResult.GetChatInfoError:
                di['text'] = '获取群/频道信息失败。'
            elif checkResult == UserPermissionsInChatCheckResult.PrivateChat:
                di['text'] = '该chat ID为私聊。'
            elif checkResult == UserPermissionsInChatCheckResult.GetChatAdministratorsError:
                di['text'] = '获取群/频道管理员列表失败。'
            elif checkResult == UserPermissionsInChatCheckResult.NoPermissions:
                di['text'] = '您没有权限进行操作。'
            self._main._request('editMessageText', 'post', json=di)


class callbackQueryHandle(Thread):
    def __init__(self, main: main, data: dict):
        Thread.__init__(self)
        self._main = main
        self._data = data

    def answer(self, text: str = ''):
        di = {}
        di['callback_query_id'] = self._callbackQueryId
        di['text'] = text
        self._main._request('answerCallbackQuery', 'post', json=di)

    def run(self):
        self._callbackQueryId = self._data['id']
        self._fromUserId = self._data['from']['id']
        if self._main._blackList.isInBlackList(self._fromUserId):
            self.answer('您已被封禁。')
            return
        l = self._data['data'].split(',')
        self._inputList = l
        try:
            self._loc = int(l[0])
            if self._loc == 0:
                if len(l) < 3:
                    self.answer('错误的按钮数据。')
                    return
                self._hashd = l[1]
                self._command = int(l[2])
        except:
            self.answer('错误的按钮数据。')
            return
        self._isOwn = self._main._setting.botOwnerList.isOwner(self._fromUserId)
        if 'message' not in self._data:
            self.answer('找不到信息。')
            return
        self._messageId = self._data['message']['message_id']
        self._messageThreadId = self._data['message']['message_thread_id'] if 'message_thread_id' in self._data['message'] else None
        if self._loc == 0:
            if self._data['message']['chat']['type'] != 'private':
                if checkUserPermissionsInChat(self._main, self._data['message']['chat']['id'], self._fromUserId) != UserPermissionsInChatCheckResult.OK:
                    self.answer('您没有权限操作')
                    return
            try:
                self._inlineKeyBoardCommand = InlineKeyBoardCallBack(
                    self._command)
            except:
                self.answer('未知的按钮。')
                return
            self._rssMeta = self._main._rssMetaList.getRSSMeta(self._hashd)
            if self._rssMeta is None:
                self.answer('找不到数据。可能已经超时。')
                return
            self._rssMeta.flushTime()
            self._userId = None
            if 'userId' in self._rssMeta.meta and self._rssMeta.meta['userId'] is not None:
                self._userId = self._rssMeta.meta['userId']
            if self._userId is not None and self._data['from']['id'] != self._userId:
                self.answer('你没有权限操作。')
            if self._inlineKeyBoardCommand == InlineKeyBoardCallBack.Subscribe:
                title = self._rssMeta.meta['title']
                url = self._rssMeta.meta['url']
                chatId = None
                if 'chatId' in self._rssMeta.meta and self._rssMeta.meta['chatId'] is not None:
                    chatId = self._rssMeta.meta['chatId']
                elif self._userId is not None:
                    chatId = self._userId
                if chatId is None:
                    self.answer('缺少发送的位置')
                    return
                config = self._rssMeta.config
                ttl = self._rssMeta.meta['ttl'] if 'ttl' in self._rssMeta.meta else None
                hashEntries = HashEntries(self._main._setting.maxCount)
                tempList = self._rssMeta.itemList.copy()
                tempList.reverse()
                for v in tempList[-self._main._setting.maxCount:]:
                    hashEntries.add(calHash(None, url, v))
                suc = self._main._db.addRSSList(
                    title, url, chatId, config, ttl, hashEntries)
                if suc:
                    self.answer('订阅成功！')
                else:
                    self.answer('订阅失败！')
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                di['text'] = getMediaInfo(
                    self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendPriview:
                chatId = None
                if 'chatId' in self._rssMeta.meta and self._rssMeta.meta['chatId'] is not None:
                    chatId = self._rssMeta.meta['chatId']
                elif self._userId is not None:
                    chatId = self._userId
                if chatId is None:
                    self.answer('找不到可以发送的聊天。')
                    return
                if len(self._rssMeta.itemList) == 0:
                    self.answer('列表为空。')
                    return
                ran = randrange(0, len(self._rssMeta.itemList))
                asuc = True
                ames = ''
                for tid in self._rssMeta.config.thread_ids.iter():
                    suc, mes = self._main._sendMessage(chatId, self._rssMeta.meta, self._rssMeta.itemList[ran], self._rssMeta.config, tid, True, True)
                    if not suc:
                        asuc = False
                        ames += f"\nThread Id: {tid} {mes}"
                if asuc:
                    self.answer(f'第{ran}条发送成功！')
                else:
                    print(ames)
                    self.answer(f'第{ran}条发送失败！{ames}')
                    self._main._request("sendMessage", "post", {
                                        "chat_id": chatId, "text": f'第{ran}条发送失败！{ames}'})
                return
            elif self._userId is not None and self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ModifyChatId:
                self._main._db.setUserStatus(
                    self._userId, userStatus.needInputChatId, self._hashd)
                di = {}
                if 'message' in self._data and self._data['message'] is not None:
                    di['chat_id'] = self._data['message']['chat']['id']
                else:
                    di['chat_id'] = self._data['from']['id']
                if self._messageThreadId is not None:
                    di['message_thread_id'] = self._messageThreadId
                di["text"] = "请输入群/频道的ID（使用 /cancle 可以取消）："
                self._main._request("sendMessage", "post", json=di)
                self.answer()
                return
            elif self._userId is not None and self._inlineKeyBoardCommand == InlineKeyBoardCallBack.BackUserId:
                self._rssMeta.meta['chatId'] = None
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                di['text'] = getMediaInfo(
                    self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS(
                    self._hashd, self._rssMeta.meta, self._isOwn)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand in [InlineKeyBoardCallBack.SettingsPage, InlineKeyBoardCallBack.DisableTopic]:
                if self._inlineKeyBoardCommand == InlineKeyBoardCallBack.DisableTopic:
                    self._rssMeta.config.thread_ids._list.clear()
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                di['text'] = getMediaInfo(
                    self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS2(
                    self._hashd, self._rssMeta.config)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.BackToNormalPage:
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                di['text'] = getMediaInfo(
                    self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS(
                    self._hashd, self._rssMeta.meta, self._isOwn)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand in [InlineKeyBoardCallBack.DisableWebPagePreview, InlineKeyBoardCallBack.ShowRSSTitle, InlineKeyBoardCallBack.ShowContentTitle, InlineKeyBoardCallBack.ShowContent, InlineKeyBoardCallBack.SendMedia, InlineKeyBoardCallBack.DisplayEntryLink, InlineKeyBoardCallBack.SendImgAsFile, InlineKeyBoardCallBack.SendUgoiraWithOriginPixFmt, InlineKeyBoardCallBack.SendUgoiraMethod, InlineKeyBoardCallBack.CompressBigImage]:
                if self._inlineKeyBoardCommand == InlineKeyBoardCallBack.DisableWebPagePreview:
                    self._rssMeta.config.disable_web_page_preview = not self._rssMeta.config.disable_web_page_preview
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ShowRSSTitle:
                    self._rssMeta.config.show_RSS_title = not self._rssMeta.config.show_RSS_title
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ShowContentTitle:
                    self._rssMeta.config.show_Content_title = not self._rssMeta.config.show_Content_title
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ShowContent:
                    self._rssMeta.config.show_content = not self._rssMeta.config.show_content
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendMedia:
                    self._rssMeta.config.send_media = not self._rssMeta.config.send_media
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.DisplayEntryLink:
                    self._rssMeta.config.display_entry_link = not self._rssMeta.config.display_entry_link
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendImgAsFile:
                    self._rssMeta.config.send_img_as_file = not self._rssMeta.config.send_img_as_file
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendUgoiraWithOriginPixFmt:
                    self._rssMeta.config.send_ugoira_with_origin_pix_fmt = not self._rssMeta.config.send_ugoira_with_origin_pix_fmt
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendUgoiraMethod:
                    self._rssMeta.config.send_ugoira_method = SendUgoiraMethod(int(self._inputList[3]))
                elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.CompressBigImage:
                    self._rssMeta.config.compress_big_image = not self._rssMeta.config.compress_big_image
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                di['text'] = getMediaInfo(
                    self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS2(
                    self._hashd, self._rssMeta.config)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.EnableTopic:
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                re = self._main.checkChatIsForum(self._rssMeta.chatId)
                if re is True:
                    di['text'] = getMediaInfo(
                        self._rssMeta.meta, self._rssMeta.config)
                    di['parse_mode'] = 'HTML'
                    di['disable_web_page_preview'] = True
                    di['reply_markup'] = getInlineKeyBoardWhenRSS4(
                        self._hashd, self._rssMeta.config)
                    self._main._request("editMessageText", "post", json=di)
                    self.answer()
                else:
                    self.answer('请先启用话题功能' if re is False else re)
                return
            elif self._userId is not None and self._inlineKeyBoardCommand in [InlineKeyBoardCallBack.AddTopicToList, InlineKeyBoardCallBack.RemoveTopicFromList]:
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                re = self._main.checkChatIsForum(self._rssMeta.chatId)
                if re is not True:
                    self.answer('请先启用话题功能' if re is False else re)
                    self._rssMeta.config.thread_ids.clear()
                    di = {'chat_id': self._rssMeta.chatId,
                          'message_id': self._rssMeta.messageId}
                    di['text'] = getMediaInfo(
                        self._rssMeta.meta, self._rssMeta.config)
                    di['parse_mode'] = 'HTML'
                    di['disable_web_page_preview'] = True
                    di['reply_markup'] = getInlineKeyBoardWhenRSS2(
                        self._hashd, self._rssMeta.config)
                    self._main._request("editMessageText", "post", json=di)
                    return
                added = self._inlineKeyBoardCommand == InlineKeyBoardCallBack.AddTopicToList
                self._main._db.setUserStatus(
                    self._userId, userStatus.needInputThreadId if added else userStatus.needRemoveThreadId, f'0,{self._hashd}')
                di = {}
                if 'message' in self._data and self._data['message'] is not None:
                    di['chat_id'] = self._data['message']['chat']['id']
                else:
                    di['chat_id'] = self._data['from']['id']
                if self._messageThreadId is not None:
                    di['message_thread_id'] = self._messageThreadId
                if added:
                    di["text"] = "请在话题内发送 /this 给机器人以添加相应话题（使用 /cancle 可以取消）："
                else:
                    di['text'] = "请在话题内发送 /this 给机器人以移除相应话题或者输入话题ID（使用 /cancle 可以取消）："
                self._main._request("sendMessage", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.EnableSendWithoutTopicId:
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                re = self._main.checkChatIsForum(self._rssMeta.chatId)
                if re is not True:
                    self.answer('请先启用话题功能' if re is False else re)
                    self._rssMeta.config.thread_ids.clear()
                    di = {'chat_id': self._rssMeta.chatId,
                          'message_id': self._rssMeta.messageId}
                    di['text'] = getMediaInfo(
                        self._rssMeta.meta, self._rssMeta.config)
                    di['parse_mode'] = 'HTML'
                    di['disable_web_page_preview'] = True
                    di['reply_markup'] = getInlineKeyBoardWhenRSS2(
                        self._hashd, self._rssMeta.config)
                    self._main._request("editMessageText", "post", json=di)
                    return
                self._rssMeta.config.thread_ids._without_id = not self._rssMeta.config.thread_ids._without_id
                di['text'] = getMediaInfo(self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS4(self._hashd, self._rssMeta.config)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            if not self._isOwn:
                self.answer('❌你没有权限操作，请与Bot主人进行PY交易以获得权限。')
                return
            if self._inlineKeyBoardCommand == InlineKeyBoardCallBack.GlobalSettingsPage:
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                di['text'] = getMediaInfo(
                    self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS3(
                    self._hashd, self._rssMeta.config)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendOriginFileName:
                self._rssMeta.config.send_origin_file_name = not self._rssMeta.config.send_origin_file_name
                di = {'chat_id': self._rssMeta.chatId,
                      'message_id': self._rssMeta.messageId}
                di['text'] = getMediaInfo(
                    self._rssMeta.meta, self._rssMeta.config)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS3(
                    self._hashd, self._rssMeta.config)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
        elif self._loc == 1:
            chatId = int(self._inputList[1])
            self._inlineKeyBoardForRSSListCommand = InlineKeyBoardForRSSList(
                int(self._inputList[2]))
            if self._data['message']['chat']['type'] != 'private':
                if checkUserPermissionsInChat(self._main, chatId, self._fromUserId) != UserPermissionsInChatCheckResult.OK:
                    self.answer('您没有权限操作')
                    return
            if self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.FirstPage:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                di['text'] = '列表如下：'
                rssList = self._main._db.getRSSListByChatId(chatId)
                di['reply_markup'] = getInlineKeyBoardForRSSList(
                    chatId, rssList)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.LastPage:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                di['text'] = '列表如下：'
                rssList = self._main._db.getRSSListByChatId(chatId)
                di['reply_markup'] = getInlineKeyBoardForRSSList(
                    chatId, rssList, lastPage=True)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.PrevPage:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                pageNum = int(self._inputList[3])
                di['text'] = '列表如下：'
                rssList = self._main._db.getRSSListByChatId(chatId)
                di['reply_markup'] = getInlineKeyBoardForRSSList(
                    chatId, rssList, pageNum-1)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.NextPage:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                pageNum = int(self._inputList[3])
                di['text'] = '列表如下：'
                rssList = self._main._db.getRSSListByChatId(chatId)
                di['reply_markup'] = getInlineKeyBoardForRSSList(
                    chatId, rssList, pageNum+1)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.Close:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                self._main._request("deleteMessage", "post", json=di)
                return
            elif self._inlineKeyBoardForRSSListCommand in [InlineKeyBoardForRSSList.Content, InlineKeyBoardForRSSList.CancleUnsubscribe, InlineKeyBoardForRSSList.BackToContentPage]:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                di['text'] = getTextContentForRSSInList(
                    rss, self._main._setting)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSInList(
                    chatId, rss, ind, self._main._setting.botOwnerList.isOwner(self._fromUserId))
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.BackToList:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForRSSList(
                    chatId, rssList, itemIndex=ind)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.Unsubscribe:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                di['text'] = getTextContentForRSSUnsubscribeInList(rss)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSUnsubscribeInList(
                    chatId, rss, ind)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.ConfirmUnsubscribe:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                rssId = int(self._inputList[4])
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('取消订阅失败：找不到该RSS。')
                else:
                    unsubscribed = self._main._db.removeItemInChatList(
                        chatId, rss.id)
                    if unsubscribed:
                        self.answer('取消订阅成功。')
                        ind = ind - 1
                    else:
                        self.answer('取消订阅失败：数据库删除失败。')
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = max(min(ind, len(rssList)), 0)
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForRSSList(
                    chatId, rssList, itemIndex=ind)
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForRSSListCommand in [InlineKeyBoardForRSSList.SettingsPage, InlineKeyBoardForRSSList.DisableTopic]:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                if self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.DisableTopic:
                    chatEntry: ChatEntry = rss.chatList[0]
                    chatEntry.config.thread_ids.clear()
                    if self._main._db.updateChatConfig(chatEntry):
                        self.answer('禁用成功。')
                    else:
                        self.answer('禁用失败。')
                di['text'] = getTextContentForRSSInList(
                    rss, self._main._setting)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSSettingsInList(
                    chatId, rss, ind)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand in [InlineKeyBoardForRSSList.DisableWebPagePreview, InlineKeyBoardForRSSList.ShowRSSTitle, InlineKeyBoardForRSSList.ShowContentTitle, InlineKeyBoardForRSSList.ShowContent, InlineKeyBoardForRSSList.SendMedia, InlineKeyBoardForRSSList.DisplayEntryLink, InlineKeyBoardForRSSList.SendImgAsFile, InlineKeyBoardForRSSList.SendUgoiraWithOriginPixFmt, InlineKeyBoardForRSSList.SendUgoiraMethod, InlineKeyBoardForRSSList.CompressBigImage]:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rssEntry = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rssEntry is None:
                    self.answer('找不到该RSS。')
                    return
                chatEntry: ChatEntry = rssEntry.chatList[0]
                config = chatEntry.config
                if self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.DisableWebPagePreview:
                    config.disable_web_page_preview = not config.disable_web_page_preview
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.ShowRSSTitle:
                    config.show_RSS_title = not config.show_RSS_title
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.ShowContentTitle:
                    config.show_Content_title = not config.show_Content_title
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.ShowContent:
                    config.show_content = not config.show_content
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.SendMedia:
                    config.send_media = not config.send_media
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.DisplayEntryLink:
                    config.display_entry_link = not config.display_entry_link
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.SendImgAsFile:
                    config.send_img_as_file = not config.send_img_as_file
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.SendUgoiraWithOriginPixFmt:
                    config.send_ugoira_with_origin_pix_fmt = not config.send_ugoira_with_origin_pix_fmt
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.SendUgoiraMethod:
                    config.send_ugoira_method = SendUgoiraMethod(int(self._inputList[5]))
                elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.CompressBigImage:
                    config.compress_big_image = not config.compress_big_image
                updated = self._main._db.updateChatConfig(chatEntry)
                if updated:
                    self.answer('修改设置成功')
                else:
                    self.answer('修改设置失败')
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                di['text'] = getTextContentForRSSInList(
                    rss, self._main._setting)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSSettingsInList(
                    chatId, rss, ind)
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.ForceUpdate:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                if self._main._db.setRSSForceUpdate(rss.id, True):
                    self.answer('已发送强制更新请求。')
                else:
                    self.answer('发送强制更新请求失败。')
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                di['text'] = getTextContentForRSSInList(
                    rss, self._main._setting)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSInList(
                    chatId, rss, ind, self._main._setting.botOwnerList.isOwner(self._fromUserId))
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForRSSListCommand in [InlineKeyBoardForRSSList.EnableTopic, InlineKeyBoardForRSSList.EnableSendWithoutTopicId]:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rssEntry = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rssEntry is None:
                    self.answer('找不到该RSS。')
                    return
                chatEntry: ChatEntry = rssEntry.chatList[0]
                re = self._main.checkChatIsForum(chatId)
                if re is not True:
                    self.answer('请先启用话题功能' if re is False else re)
                    if chatEntry.config.thread_ids.isEnabled:
                        chatEntry.config.thread_ids.clear()
                        self._main._db.updateChatConfig(chatEntry)
                    if self._inlineKeyBoardForRSSListCommand != InlineKeyBoardForRSSList.EnableTopic:
                        di['text'] = getTextContentForRSSInList(rssEntry, self._main._setting)
                        di['parse_mode'] = 'HTML'
                        di['reply_markup'] = getInlineKeyBoardForRSSSettingsInList(
                            chatId, rssEntry, ind)
                        self._main._request("editMessageText", "post", json=di)
                    return
                if self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.EnableSendWithoutTopicId:
                    chatEntry.config.thread_ids._without_id = not chatEntry.config.thread_ids._without_id
                    if self._main._db.updateChatConfig(chatEntry):
                        self.answer('修改设置成功')
                    else:
                        self.answer('修改设置失败')
                di['text'] = getTextContentForRSSInList(
                    rssEntry, self._main._setting)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSThreadIdsInList(
                    chatId, rssEntry, ind)
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForRSSListCommand in [InlineKeyBoardForRSSList.AddTopicToList, InlineKeyBoardForRSSList.RemoveTopicFromList]:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rssEntry = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rssEntry is None:
                    self.answer('找不到该RSS。')
                    return
                chatEntry: ChatEntry = rssEntry.chatList[0]
                re = self._main.checkChatIsForum(chatId)
                if re is not True:
                    self.answer('请先启用话题功能' if re is False else re)
                    if chatEntry.config.thread_ids.isEnabled:
                        chatEntry.config.thread_ids.clear()
                        self._main._db.updateChatConfig(chatEntry)
                    di['text'] = getTextContentForRSSInList(rssEntry, self._main._setting)
                    di['parse_mode'] = 'HTML'
                    di['reply_markup'] = getInlineKeyBoardForRSSSettingsInList(
                        chatId, rssEntry, ind)
                    self._main._request("editMessageText", "post", json=di)
                    return
                added = self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.AddTopicToList
                self._main._db.setUserStatus(
                    self._fromUserId, userStatus.needInputThreadId if added else userStatus.needRemoveThreadId, f'1,{chatId},{self._messageId},{ind},{rssId}')
                di = {}
                if 'message' in self._data and self._data['message'] is not None:
                    di['chat_id'] = self._data['message']['chat']['id']
                else:
                    di['chat_id'] = self._data['from']['id']
                if self._messageThreadId is not None:
                    di['message_thread_id'] = self._messageThreadId
                if added:
                    di["text"] = "请在话题内发送 /this 给机器人以添加相应话题（使用 /cancle 可以取消）："
                else:
                    di['text'] = "请在话题内发送 /this 给机器人以移除相应话题或者输入话题ID（使用 /cancle 可以取消）："
                self._main._request("sendMessage", "post", json=di)
                self.answer()
                return
            if not self._isOwn:
                self.answer('❌你没有权限操作，请与Bot主人进行PY交易以获得权限。')
                return
            if self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.GlobalSettingsPage:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                di['text'] = getTextContentForRSSInList(
                    rss, self._main._setting)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSGlobalSettingsInList(chatId, rss, ind)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.SendOriginFileName:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(ind, 0)
                rssId = int(self._inputList[4])
                rssEntry = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rssEntry is None:
                    self.answer('找不到该RSS。')
                    return
                chatEntry: ChatEntry = rssEntry.chatList[0]
                config = chatEntry.config
                config.send_origin_file_name = not config.send_origin_file_name
                updated = self._main._db.updateRSSSettings(rssEntry.id, config)
                if updated:
                    self.answer('修改设置成功')
                else:
                    self.answer('修改设置失败')
                rss = self._main._db.getRSSByIdAndChatId(rssId, chatId)
                if rss is None:
                    self.answer('找不到该RSS。')
                    return
                di['text'] = getTextContentForRSSInList(
                    rss, self._main._setting)
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSGlobalSettingsInList(chatId, rss, ind)
                self._main._request("editMessageText", "post", json=di)
                return
        elif self._loc == 2:
            if self._fromUserId is None or not self._isOwn:
                self.answer('❌你没有权限操作，请与Bot主人进行PY交易以获得权限。')
                return
            try:
                self._inlineKeyBoardForBlackListCommand = InlineKeyBoardForBlackList(int(self._inputList[1]))
            except Exception:
                self.answer('未知的按钮。')
                return
            di = {'chat_id': self._data['message']['chat']['id'],
                  'message_id': self._data['message']['message_id']}
            if self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.FirstPage:
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForBlackList(self._main._blackList.getBlackList())
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.LastPage:
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForBlackList(self._main._blackList.getBlackList(), lastPage=True)
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.PrevPage:
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForBlackList(self._main._blackList.getBlackList(), int(self._inputList[2]) - 1)
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.NextPage:
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForBlackList(self._main._blackList.getBlackList(), int(self._inputList[2]) + 1)
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.Close:
                self._main._request("deleteMessage", "post", json=di)
                return
            elif self._inlineKeyBoardForBlackListCommand in [InlineKeyBoardForBlackList.BlackInfo, InlineKeyBoardForBlackList.CancleUnban]:
                bl = self._main._blackList.getBlackList()
                ind = bl.find(int(self._inputList[3]))
                if ind == -1:
                    self.answer('在黑名单里找不到该用户。')
                    di['text'] = '列表如下：'
                    di['reply_markup'] = getInlineKeyBoardForBlackList(bl, itemIndex=int(self._inputList[2]))
                    self._main._request("editMessageText", "post", json=di)
                    return
                else:
                    di['text'] = getTextContentForBlackInfo(bl[ind])
                    di['parse_mode'] = 'HTML'
                    di['reply_markup'] = getInlineKeyBoardForBlackInfo(bl[ind], ind)
                    self._main._request("editMessageText", "post", json=di)
                    return
            elif self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.BackToList:
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForBlackList(self._main._blackList.getBlackList(), itemIndex=int(self._inputList[2]))
                self._main._request("editMessageText", "post", json=di)
                return
            elif self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.Unban:
                bl = self._main._blackList.getBlackList()
                ind = bl.find(int(self._inputList[3]))
                if ind == -1:
                    self.answer('在黑名单里找不到该用户。')
                    di['text'] = '列表如下：'
                    di['reply_markup'] = getInlineKeyBoardForBlackList(bl, itemIndex=int(self._inputList[2]))
                    self._main._request("editMessageText", "post", json=di)
                    return
                else:
                    if bl[ind].from_config:
                        self.answer('无法取消封禁来自配置文件的用户，请修改配置文件后重启bot。')
                        return
                    di['text'] = getTextContentForUnbanBlackInfo(bl[ind])
                    di['parse_mode'] = 'HTML'
                    di['reply_markup'] = getInlineKeyBoardForUnbanBlackInfo(bl[ind], ind)
                    self._main._request("editMessageText", "post", json=di)
                    return
            elif self._inlineKeyBoardForBlackListCommand == InlineKeyBoardForBlackList.ConfirmUnban:
                bl = self._main._blackList.getBlackList()
                ind = bl.find(int(self._inputList[3]))
                if ind == -1:
                    self.answer('在黑名单里找不到该用户。')
                else:
                    if bl[ind].from_config:
                        self.answer('无法取消封禁来自配置文件的用户，请修改配置文件后重启bot。')
                        return
                    re = self._main._blackList.unban(bl[ind].uid)
                    self.answer('取消封禁' + ('成功！' if re else '失败！'))
                di['text'] = '列表如下：'
                di['reply_markup'] = getInlineKeyBoardForBlackList(self._main._blackList.getBlackList(), itemIndex=int(self._inputList[2]))
                self._main._request("editMessageText", "post", json=di)
                return
        elif self._loc == 3:
            if self._fromUserId is None or not self._isOwn:
                self.answer('❌你没有权限操作，请与Bot主人进行PY交易以获得权限。')
                return
            try:
                self._inlineKeyBoardForManageCommand = InlineKeyBoardForManage(int(self._inputList[1]))
            except Exception:
                self.answer('未知的按钮。')
                return
            di = {'chat_id': self._data['message']['chat']['id'],
                  'message_id': self._data['message']['message_id']}
            if self._inlineKeyBoardForManageCommand == InlineKeyBoardForManage.Close:
                self._main._request("deleteMessage", "post", json=di)
                return
            elif self._inlineKeyBoardForManageCommand in [InlineKeyBoardForManage.ManageByRSS, InlineKeyBoardForManage.ManageByChatId]:
                innerCommand = None
                is_rss_manage = False
                rssManageCommand = None
                rssManageChatIndex = None
                rssManageChatId = None
                rssManageRSSId = None
                rssManageIndex = None
                rssManageSubList = None
                if len(self._inputList) > 2:
                    try:
                        innerCommand = InlineKeyBoardForManage(int(self._inputList[2]))
                    except Exception:
                        self.answer('未知的按钮。')
                        return
                if innerCommand is None or innerCommand in [InlineKeyBoardForManage.FirstPage, InlineKeyBoardForManage.LastPage, InlineKeyBoardForManage.NextPage, InlineKeyBoardForManage.PrevPage, InlineKeyBoardForManage.BackToList]:
                    page = 1
                    lastPage = False
                    itemIndex = None
                    if innerCommand == InlineKeyBoardForManage.LastPage:
                        lastPage = True
                    elif innerCommand == InlineKeyBoardForManage.NextPage:
                        page = int(self._inputList[3]) + 1
                    elif innerCommand == InlineKeyBoardForManage.PrevPage:
                        page = int(self._inputList[3]) - 1
                    elif innerCommand == InlineKeyBoardForManage.BackToList:
                        itemIndex = int(self._inputList[3])
                    if self._inlineKeyBoardForManageCommand == InlineKeyBoardForManage.ManageByRSS:
                        rssList = self._main._db.getRSSList()
                        di['text'] = '列表如下：'
                        di['reply_markup'] = getInlineKeyBoardForManageRSSList(rssList, page, lastPage, itemIndex)
                        self._main._request("editMessageText", "post", json=di)
                        return
                    else:
                        chatList = self._main._db.getChatIdList()
                        di['text'] = '列表如下：'
                        di['reply_markup'] = getInlineKeyBoardForManageChatList(self._main, chatList, page, lastPage, itemIndex)
                        self._main._request("editMessageText", "post", json=di)
                        return
                elif innerCommand == InlineKeyBoardForManage.ChatManage:
                    innerCommand2 = None
                    try:
                        index = max(int(self._inputList[3]), 0)
                        chat_id = int(self._inputList[4])
                    except Exception:
                        self.answer('未知的按钮。')
                        return
                    if len(self._inputList) > 5:
                        try:
                            innerCommand2 = InlineKeyBoardForManage(int(self._inputList[5]))
                        except Exception:
                            self.answer('未知的按钮。')
                            return
                    if innerCommand2 is None or innerCommand2 in [InlineKeyBoardForManage.FirstPage, InlineKeyBoardForManage.LastPage, InlineKeyBoardForManage.NextPage, InlineKeyBoardForManage.PrevPage, InlineKeyBoardForManage.BackToList]:
                        page = 1
                        lastPage = False
                        itemIndex = None
                        if innerCommand2 == InlineKeyBoardForManage.LastPage:
                            lastPage = True
                        elif innerCommand2 == InlineKeyBoardForManage.NextPage:
                            page = int(self._inputList[6]) + 1
                        elif innerCommand2 == InlineKeyBoardForManage.PrevPage:
                            page = int(self._inputList[6]) - 1
                        elif innerCommand2 == InlineKeyBoardForManage.BackToList:
                            itemIndex = int(self._inputList[6])
                        rssList = self._main._db.getRSSListByChatId(chat_id)
                        di['text'] = '列表如下：'
                        di['reply_markup'] = getInlineKeyBoardForManageRSSList(rssList, page, lastPage, itemIndex, base=f"3,{InlineKeyBoardForManage.ManageByChatId.value},{InlineKeyBoardForManage.ChatManage.value},{index},{chat_id}", back=f"3,{InlineKeyBoardForManage.ManageByChatId.value},{InlineKeyBoardForManage.BackToList.value},{index}")
                        self._main._request("editMessageText", "post", json=di)
                        return
                    elif innerCommand2 == InlineKeyBoardForManage.RSSManage:
                        try:
                            rssManageIndex = int(self._inputList[6])
                            rssManageRSSId = int(self._inputList[7])
                        except Exception:
                            self.answer('未知的按钮。')
                            return
                        rssManageChatId = chat_id
                        rssManageChatIndex = index
                        if len(self._inputList) > 8:
                            try:
                                rssManageCommand = InlineKeyBoardForManage(int(self._inputList[8]))
                            except Exception:
                                self.answer('未知的按钮。')
                                return
                        if len(self._inputList) > 9:
                            rssManageSubList = self._inputList[9:]
                        is_rss_manage = True
                elif innerCommand == InlineKeyBoardForManage.RSSManage:
                    is_rss_manage = True
                    try:
                        rssManageIndex = int(self._inputList[3])
                        rssManageRSSId = int(self._inputList[4])
                    except:
                        self.answer('未知的按钮。')
                        return
                    if len(self._inputList) > 5:
                        try:
                            rssManageCommand = InlineKeyBoardForManage(int(self._inputList[5]))
                        except Exception:
                            self.answer('未知的按钮。')
                            return
                    if len(self._inputList) > 6:
                        rssManageSubList = self._inputList[6:]
                if is_rss_manage:
                    if rssManageChatId is not None:
                        rssEntry = self._main._db.getRSSByIdAndChatId(rssManageRSSId, rssManageChatId)
                    else:
                        rssEntry = self._main._db.getRSSById(rssManageRSSId)
                    if rssManageCommand is None:
                        di['text'] = getTextContentForRSSInManageList(self._main, rssEntry, self._main._setting, rssManageChatId)
                        di['parse_mode'] = 'HTML'
                        di['reply_markup'] = getInlineKeyBoardForRSSInManageList(rssEntry, rssManageIndex, rssManageChatId, rssManageChatIndex)
                        self._main._request("editMessageText", "post", json=di)
                        return
                    elif rssManageCommand == InlineKeyBoardForManage.Unsubscribe:
                        di['text'] = getTextContentForRSSUnsubscribeInList(rssEntry)
                        di['parse_mode'] = 'HTML'
                        di['reply_markup'] = getInlineKeyBoardForRSSUnsubscribeInManageList(rssEntry, rssManageIndex, rssManageChatId, rssManageChatIndex)
                        self._main._request("editMessageText", "post", json=di)
                        return
            elif self._inlineKeyBoardForManageCommand == InlineKeyBoardForManage.ManageMenu:
                di['text'] = '请选择管理模式：'
                di['reply_markup'] = getInlineKeyBoardForManage()
                self._main._request("editMessageText", "post", json=di)
                return
        else:
            self.answer('未知的按钮。')
            return
        self.answer('未知的按钮。')


if __name__ == "__main__":
    m = main()
    m.start()
