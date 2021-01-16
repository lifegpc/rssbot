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
from database import database, userStatus, RSSConfig
from RSSEntry import HashEntry, HashEntries, calHash, ChatEntry
from os.path import exists
from readset import settings, commandline
from requests import Session
from traceback import format_exc
from threading import Thread
from typing import List
from rssparser import RSSParser
from html import escape
from hashl import md5WithBase64
from enum import Enum, unique
from rsstempdict import rssMetaInfo, rssMetaList
from random import randrange
from textc import textc, removeEmptyLine, decodeURI
from re import search, I
from rsschecker import RSSCheckerThread
from rsslist import getInlineKeyBoardForRSSList, InlineKeyBoardForRSSList, getInlineKeyBoardForRSSInList, getTextContentForRSSInList, getInlineKeyBoardForRSSUnsubscribeInList, getTextContentForRSSUnsubscribeInList, getInlineKeyBoardForRSSSettingsInList
from usercheck import checkUserPermissionsInChat, UserPermissionsInChatCheckResult
import sys
from fileEntry import FileEntries, remove
from dictdeal import json2data
from rssbotlib import loadRSSBotLib, AddVideoInfoResult


def getMediaInfo(m: dict, config: RSSConfig = RSSConfig()) -> str:
    s = ''
    if 'link' in m:
        s = f"""{s}标题：<a href="{m['link']}">{escape(m['title'])}</a>"""
    else:
        s = f"{s}标题：{escape(m['title'])}"
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


def getInlineKeyBoardWhenRSS(hashd: str, m: dict) -> dict:
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
    d[i].append(
        {'text': '返回', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.BackToNormalPage.value}'})
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
                HTTPMethod, f'{self._telegramBotApiServer if telegramBotApiServer is None else telegramBotApiServer}/bot{self._setting._token}/{methodName}', data=data, json=json, files=files)
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

    def _sendMessage(self, chatId: int, meta: dict, content: dict, config: RSSConfig, returnError: bool = False):
        with self._tempFileEntries._value_lock:
            return self.__sendMessage(chatId, meta, content, config, returnError)

    def __sendMessage(self, chatId: int, meta: dict, content: dict, config: RSSConfig, returnError: bool = False):
        di = {}
        di['chat_id'] = chatId
        text = textc()
        if config.show_RSS_title:
            text.addtotext(f"<b>{escape(meta['title'])}</b>")
        if config.show_Content_title and 'title' in content and content['title'] is not None and content['title'] != '':
            if 'link' in content and content['link'] is not None and content['link'] != '':
                text.addtotext(
                    f"""<b><a href="{content['link']}">{escape(content['title'])}</a></b>""")
            else:
                text.addtotext(f"<b>{escape(content['title'])}</b>")
        elif 'link' in content and content['link'] is not None and content['link'] != '':
            text.addtotext(
                f"""<a href="{content['link']}">{escape(content['link'])}</a>""")
        if config.show_content and 'description' in content and content['description'] is not None and content['description'] != '':
            text.addtotext(removeEmptyLine(content['description']))

        def getListCount(content: dict, key: str):
            if key not in content or content[key] is None:
                return 0
            return len(content[key])
        if not config.send_media or (getListCount(content, 'imgList') == 0 and getListCount(content, 'videoList') == 0):
            if config.disable_web_page_preview:
                di['disable_web_page_preview'] = True
            di['text'] = text.tostr()
            di['parse_mode'] = 'HTML'
            re = self._request('sendMessage', 'post', json=di)
        elif getListCount(content, 'imgList') == 1 and getListCount(content, 'videoList') == 0:
            di['caption'] = text.tostr()
            di['parse_mode'] = 'HTML'
            if not self._setting._downloadMediaFile:
                di['photo'] = content['imgList'][0]
                re = self._request('sendPhoto', 'post', json=di)
            else:
                fileEntry = self._tempFileEntries.add(content['imgList'][0])
                if not fileEntry.ok:
                    return None
                if self._setting._sendFileURLScheme:
                    di['photo'] = fileEntry._localURI
                    re = self._request('sendPhoto', 'post', json=di)
                else:
                    fileEntry.open()
                    re = self._request('sendPhoto', 'post', json=di, files={
                                       'photo': (fileEntry._fullfn, fileEntry._f)})
        elif getListCount(content, 'imgList') == 0 and getListCount(content, 'videoList') == 1:
            di['caption'] = text.tostr()
            di['parse_mode'] = 'HTML'
            if self._setting._downloadMediaFile and not self._setting._sendFileURLScheme:
                di2 = {}
            if not self._setting._downloadMediaFile:
                di['video'] = content['videoList'][0]['src']
            else:
                fileEntry = self._tempFileEntries.add(
                    content['videoList'][0]['src'])
                if not fileEntry.ok:
                    return None
                if self._setting._sendFileURLScheme:
                    di['video'] = fileEntry._localURI
                else:
                    fileEntry.open()
                    di2['video'] = (fileEntry._fullfn, fileEntry._f)
            if 'poster' in content['videoList'][0] and content['videoList'][0]['poster'] is not None and content['videoList'][0]['poster'] != '':
                if not self._setting._downloadMediaFile:
                    di['thumb'] = content['videoList'][0]['poster']
                else:
                    fileEntry = self._tempFileEntries.add(
                        content['videoList'][0]['poster'])
                    if not fileEntry.ok:
                        return False
                    if self._setting._sendFileURLScheme:
                        di['thumb'] = fileEntry._localURI
                    else:
                        fileEntry.open()
                        di2['thumb'] = (fileEntry._fullfn, fileEntry._f)
            di['supports_streaming'] = True
            isOk = True
            if self._rssbotLib is not None:
                loc = self._tempFileEntries.get(content['videoList'][0]['src'])._abspath if self._setting._downloadMediaFile and self._tempFileEntries.get(
                    content['videoList'][0]['src']) is not None else None
                addre = self._rssbotLib.addVideoInfo(
                    content['videoList'][0]['src'], di, loc)
                if addre == AddVideoInfoResult.IsHLS:
                    isOk = False
                    del di['video']
                    del di['thumb']
                    del di['supports_streaming']
                    di['text'] = di['caption']
                    del di['caption']
                    if config.disable_web_page_preview:
                        di['disable_web_page_preview'] = True
                    re = self._request('sendMessage', 'post', json=di)
            if isOk:
                if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                    re = self._request('sendVideo', 'post', json=di)
                else:
                    re = self._request('sendVideo', 'post', json=di, files=di2)
        else:
            ind = 0
            if self._setting._downloadMediaFile and not self._setting._sendFileURLScheme:
                ind2 = 0
                di3 = {}
            di['media'] = []
            for i in content['imgList']:
                if ind % 9 == 0 and ind != 0:
                    if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                        re = self._request('sendMediaGroup', 'post', json=di)
                        di['media'] = []
                    else:
                        re = self._request(
                            'sendMediaGroup', 'post', json=di, files=di3)
                        di['media'] = []
                        di3 = {}
                di2 = {'type': 'photo'}
                if not self._setting._downloadMediaFile:
                    di2['media'] = i
                else:
                    fileEntry = self._tempFileEntries.add(i)
                    if not fileEntry.ok:
                        return None
                    if self._setting._sendFileURLScheme:
                        di2['media'] = fileEntry._localURI
                    else:
                        fileEntry.open()
                        di2['media'] = f'attach://file{ind2}'
                        di3[f'file{ind2}'] = (fileEntry._fullfn, fileEntry._f)
                        ind2 = ind2 + 1
                if ind == 0:
                    di2['caption'] = text.tostr()
                    di2['parse_mode'] = 'HTML'
                di['media'].append(di2)
                ind = ind + 1
            for i in content['videoList']:
                if ind % 9 == 0 and ind != 0:
                    if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                        re = self._request('sendMediaGroup', 'post', json=di)
                        di['media'] = []
                    else:
                        re = self._request(
                            'sendMediaGroup', 'post', json=di, files=di3)
                        di['media'] = []
                        di3 = {}
                di2 = {'type': 'video', 'supports_streaming': True}
                if not self._setting._downloadMediaFile:
                    di2['media'] = i['src']
                else:
                    fileEntry = self._tempFileEntries.add(i['src'])
                    if not fileEntry.ok:
                        return None
                    if self._setting._sendFileURLScheme:
                        di2['media'] = fileEntry._localURI
                    else:
                        fileEntry.open()
                        di2['media'] = f'attach://file{ind2}'
                        di3[f'file{ind2}'] = (fileEntry._fullfn, fileEntry._f)
                        ind2 = ind2 + 1
                if 'poster' in i and i['poster'] is not None and i['poster'] != '':
                    if not self._setting._downloadMediaFile:
                        di2['thumb'] = i['poster']
                    else:
                        fileEntry = self._tempFileEntries.add(i['poster'])
                        if not fileEntry.ok:
                            return None
                        if self._setting._sendFileURLScheme:
                            di2['thumb'] = fileEntry._localURI
                        else:
                            fileEntry.open()
                            di2['thumb'] = f'attach://file{ind2}'
                            di3[f'file{ind2}'] = (
                                fileEntry._fullfn, fileEntry._f)
                            ind2 = ind2 + 1
                if ind == 0:
                    di2['caption'] = text.tostr()
                    di2['parse_mode'] = 'HTML'
                if self._rssbotLib is not None:
                    loc = self._tempFileEntries.get(i['src'])._abspath if self._setting._downloadMediaFile and self._tempFileEntries.get(
                        i['src']) is not None else None
                    addre = self._rssbotLib.addVideoInfo(i['src'], di2, loc)
                    if addre == AddVideoInfoResult.IsHLS:
                        continue
                di['media'].append(di2)
                ind = ind + 1
            if len(di['media']) > 1:
                if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                    re = self._request('sendMediaGroup', 'post', json=di)
                else:
                    re = self._request(
                        'sendMediaGroup', 'post', json=di, files=di3)
            if len(di['media']) == 1:
                if di['media'][0]['type'] == 'photo':
                    if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                        di['photo'] = di['media'][0]['media']
                    else:
                        mekey = di['media'][0]['media'][9:]
                        di3['photo'] = di3[mekey]
                        del di3[mekey]
                    del di['media']
                    if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                        re = self._request('sendPhoto', 'post', json=di)
                    else:
                        re = self._request(
                            'sendPhoto', 'post', json=di, files=di3)
                elif di['media'][0]['type'] == 'video':
                    if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                        di['video'] = di['media'][0]['media']
                        if 'thumb' in di['media'][0]:
                            di['thumb'] = di['media'][0]['thumb']
                    else:
                        mekey = di['media'][0]['media'][9:]
                        di3['video'] = di3[mekey]
                        del di3[mekey]
                        if 'thumb' in di['media'][0]:
                            mekey = di['media'][0]['thumb'][9:]
                            di3['thumb'] = di3[mekey]
                            del di3[mekey]
                    if 'duration' in di['media'][0]:
                        di['duration'] = di['media'][0]['duration']
                    if 'width' in di['media'][0]:
                        di['width'] = di['media'][0]['width']
                    if 'height' in di['media'][0]:
                        di['height'] = di['media'][0]['height']
                    di['supports_streaming'] = di['media'][0]['supports_streaming']
                    del di['media']
                    if not self._setting._downloadMediaFile or self._setting._sendFileURLScheme:
                        re = self._request('sendVideo', 'post', json=di)
                    else:
                        re = self._request(
                            'sendVideo', 'post', json=di, files=di3)
        if re is not None and 'ok' in re and re['ok']:
            if returnError:
                return True, ''
            return True
        if returnError and re is not None and 'description' in re:
            return False, re['description']
        elif returnError:
            return False, ''
        return False

    def _updateLoop(self):
        d = {'allowed_updates': ['message', 'edited_message',
                                 'channel_post', 'edited_channel_post', 'callback_query']}
        if self._upi is not None:
            d['offset'] = self._upi
        ud = self._request('getUpdates', 'post', json=d)
        print(ud)
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

    def start(self):
        self._setting = settings('settings.txt')
        if self._setting._token is None:
            print('没有机器人token')
            return -1
        self._commandLine = commandline()
        if len(sys.argv) > 1:
            self._commandLine.parse(sys.argv[1:])
        self._telegramBotApiServer = self._setting._telegramBotApiServer
        self._db = database(self)
        if not exists('settings.txt'):
            print('找不到settings.txt')
            return -1
        self._r = Session()
        if self._telegramBotApiServer != 'https://api.telegram.org':
            self._request("logOut", "post",
                          telegramBotApiServer="https://api.telegram.org")
        remove('Temp')
        self._tempFileEntries = FileEntries()
        self._me = self._request('getMe')
        self._rssMetaList = rssMetaList()
        print(self._me)
        if self._me is None or 'ok' not in self._me or not self._me['ok']:
            print('无法读取机器人信息')
        self._me = self._me['result']
        self._rssbotLib = loadRSSBotLib(self._setting._rssbotLib, self)
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
        while True:
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
        if self._chatId is None:
            print('未知的chat id')
            return -1
        self._botCommand = None
        if 'text' in self._data:
            if 'entities' in self._data:
                self._botCommand = self.__getBotCommand()
        self._fromUserId = self.__getFromUserId()
        if self._fromUserId is not None:
            di = {'chat_id': self._chatId}
            if self.__getChatType() in ['supergroup', 'group'] and self._fromUserId is not None:
                di['reply_to_message_id'] = self._messageId
            self._userStatus, self._hashd = self._main._db.getUserStatus(
                self._fromUserId)
            if self._userStatus == userStatus.normalStatus:
                pass
            elif self._botCommand is not None and self._botCommand == '/cancle':
                if self._userStatus == userStatus.needInputChatId:
                    di['text'] = '已取消输入群/频道ID。'
                self._main._db.setUserStatus(
                    self._fromUserId, userStatus.normalStatus)
                self._main._request('sendMessage', 'post', json=di)
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
                                    if re2['type'] == 'channel' and chatMember['status'] == 'administrator' and ('can_edit_messages' not in chatMember or not chatMember['can_edit_messages']):
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
                                    if re2['type'] == 'channel' and (re4['status'] not in ['creator', 'administrator'] or not re4['can_post_messages'] or not re4['can_edit_messages']):
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
                            self._hashd, metainfo.meta)
                        self._main._request('editMessageText', 'post', json=di)
                        self._main._db.setUserStatus(
                            self._fromUserId, userStatus.normalStatus)
                    return
        if self._botCommand is None and self._data['chat']['type'] in ['group', 'supergroup']:
            return
        if self._botCommand is None or self._botCommand not in ['/help', '/rss', '/rsslist']:
            self._botCommand = '/help'
        di = {'chat_id': self._chatId}
        if self.__getChatType() in ['supergroup', 'group'] and self._fromUserId is not None:
            di['reply_to_message_id'] = self._messageId
        if self._botCommand == '/help':
            di['text'] = '''/help   显示帮助
/rss url    订阅RSS
/rsslist [chatId]   获取RSS订阅列表'''
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
        re = self._main._request('sendMessage', 'post', json=di)
        if self._botCommand == '/rss' and self._uri is not None and re is not None and 'ok' in re and re['ok']:
            re = re['result']
            chatId = re['chat']['id']
            messageId = re['message_id']
            di = {'chat_id': chatId, 'message_id': messageId}
            checked = False
            try:
                p = RSSParser()
                p.parse(self._uri)
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
                    self._hash, media)
                self._main._rssMetaList.addRSSMeta(rssMetaInfo(
                    re['message_id'], chatId, media, p.itemList, self._hash))
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
        l = self._data['data'].split(',')
        if len(l) < 3:
            self.answer('错误的按钮数据。')
            return
        self._inputList = l
        try:
            self._loc = int(l[0])
            if self._loc == 0:
                self._hashd = l[1]
                self._command = int(l[2])
        except:
            self.answer('错误的按钮数据。')
            return
        if self._loc == 0:
            if 'message' not in self._data:
                self.answer('找不到信息。')
                return
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
                hashEntries = HashEntries(self._main._setting._maxCount)
                tempList = self._rssMeta.itemList.copy()
                tempList.reverse()
                for v in tempList[-self._main._setting._maxCount:]:
                    hashEntries.add(calHash(url, v))
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
                suc, mes = self._main._sendMessage(
                    chatId, self._rssMeta.meta, self._rssMeta.itemList[ran], self._rssMeta.config, True)
                if suc:
                    self.answer(f'第{ran}条发送成功！')
                else:
                    print(mes)
                    self.answer(f'第{ran}条发送失败！{mes}')
                    self._main._request("sendMessage", "post", {
                                        "chat_id": chatId, "text": f'第{ran}条发送失败！{mes}'})
                return
            elif self._userId is not None and self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ModifyChatId:
                self._main._db.setUserStatus(
                    self._userId, userStatus.needInputChatId, self._hashd)
                di = {}
                if 'message' in self._data and self._data['message'] is not None:
                    di['chat_id'] = self._data['message']['chat']['id']
                else:
                    di['chat_id'] = self._data['from']['id']
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
                    self._hashd, self._rssMeta.meta)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SettingsPage:
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
                    self._hashd, self._rssMeta.meta)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.DisableWebPagePreview:
                self._rssMeta.config.disable_web_page_preview = not self._rssMeta.config.disable_web_page_preview
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
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ShowRSSTitle:
                self._rssMeta.config.show_RSS_title = not self._rssMeta.config.show_RSS_title
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
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ShowContentTitle:
                self._rssMeta.config.show_Content_title = not self._rssMeta.config.show_Content_title
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
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ShowContent:
                self._rssMeta.config.show_content = not self._rssMeta.config.show_content
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
            elif self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendMedia:
                self._rssMeta.config.send_media = not self._rssMeta.config.send_media
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
        elif self._loc == 1:
            chatId = int(self._inputList[1])
            self._inlineKeyBoardForRSSListCommand = InlineKeyBoardForRSSList(
                int(self._inputList[2]))
            if 'message' not in self._data:
                self.answer('找不到信息。')
                return
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
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(min(ind, len(rssList)), 0)
                di['text'] = getTextContentForRSSInList(rssList[ind])
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSInList(
                    chatId, rssList[ind], ind)
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
                ind = max(min(ind, len(rssList)), 0)
                di['text'] = getTextContentForRSSUnsubscribeInList(
                    rssList[ind])
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSUnsubscribeInList(
                    chatId, rssList[ind], ind)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.ConfirmUnsubscribe:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                if ind >= len(rssList) or ind < 0:
                    self.answer('取消订阅失败：无效的索引。')
                else:
                    unsubscribed = self._main._db.removeItemInChatList(
                        chatId, rssList[ind].id)
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
            elif self._inlineKeyBoardForRSSListCommand == InlineKeyBoardForRSSList.SettingsPage:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(min(ind, len(rssList)), 0)
                di['text'] = getTextContentForRSSInList(rssList[ind])
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSSettingsInList(
                    chatId, rssList[ind], ind)
                self._main._request("editMessageText", "post", json=di)
                self.answer()
                return
            elif self._inlineKeyBoardForRSSListCommand in [InlineKeyBoardForRSSList.DisableWebPagePreview, InlineKeyBoardForRSSList.ShowRSSTitle, InlineKeyBoardForRSSList.ShowContentTitle, InlineKeyBoardForRSSList.ShowContent, InlineKeyBoardForRSSList.SendMedia]:
                di = {'chat_id': self._data['message']['chat']['id'],
                      'message_id': self._data['message']['message_id']}
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = int(self._inputList[3])
                ind = max(min(ind, len(rssList)), 0)
                rssEntry = rssList[ind]
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
                updated = self._main._db.updateChatConfig(chatEntry)
                if updated:
                    self.answer('修改设置成功')
                else:
                    self.answer('修改设置失败')
                rssList = self._main._db.getRSSListByChatId(chatId)
                ind = max(min(ind, len(rssList)), 0)
                di['text'] = getTextContentForRSSInList(rssList[ind])
                di['parse_mode'] = 'HTML'
                di['reply_markup'] = getInlineKeyBoardForRSSSettingsInList(
                    chatId, rssList[ind], ind)
                self._main._request("editMessageText", "post", json=di)
                return
        else:
            self.answer('未知的按钮。')
            return


if __name__ == "__main__":
    m = main()
    m.start()
