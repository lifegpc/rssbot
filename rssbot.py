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
from os.path import exists
from readset import settings
from requests import Session
from traceback import format_exc
from threading import Thread
from typing import List
from rssparser import RSSParser
from html import escape
from hashl import md5WithBase64
from enum import Enum
from rsstempdict import rssMetaInfo, rssMetaList
from random import randrange
from textc import textc


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
    return s


class InlineKeyBoardCallBack(Enum):
    Subscribe = 0
    SendPriview = 1
    ModifyChatId = 2
    BackUserId = 3


def getInlineKeyBoardWhenRSS(hashd: str, m: dict) -> str:
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
            d.append([])
            i = i + 1
            d[i].append(
                {'text': '发送至私聊', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.BackUserId.value}'})
    elif 'userId' in m and m['userId'] is not None:
        d.append([])
        i = i + 1
        d[i].append(
            {'text': '发送至群组/频道', 'callback_data': f'0,{hashd},{InlineKeyBoardCallBack.ModifyChatId.value}'})
    return {'inline_keyboard': d}


class main:
    def __init__(self):
        pass

    def _request(self, methodName: str, HTTPMethod: str = 'get', data: dict = None, json: dict = None, files: dict = None, returnType: str = 'json'):
        try:
            r = self._r.request(
                HTTPMethod, f'https://api.telegram.org/bot{self._setting._token}/{methodName}', data=data, json=json, files=files)
            if r.status_code != 200:
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

    def _sendMessage(self, chatId: int, meta: dict, content: dict, config: RSSConfig):
        di = {}
        di['chat_id'] = chatId
        text = textc()
        if config.show_RSS_title:
            text.addtotext(f"<b>{escape(meta['title'])}</b>")
        if config.show_Content_title and 'title' in content and content['title'] is not None and content['title'] != '':
            if 'link' in content:
                text.addtotext(
                    f"""<b><a href="{content['link']}">{escape(content['title'])}</a></b>""")
            else:
                text.addtotext(f"<b>{escape(content['title'])}</b>")
        if 'description' in content and content['description'] is not None and content['description'] != '':
            text.addtotext(content['description'])

        def getListCount(content: dict, key: str):
            if key not in content and content[key] is None:
                return 0
            return len(content[key])
        if getListCount(content, 'imgList') == 0 and getListCount(content, 'videoList') == 0:
            if config.disable_web_page_preview:
                di['disable_web_page_preview'] = True
            di['text'] = text.tostr()
            di['parse_mode'] = 'HTML'
            re = self._request('sendMessage', 'post', json=di)
        elif getListCount(content, 'imgList') == 1 and getListCount(content, 'videoList') == 0:
            di['caption'] = text.tostr()
            di['parse_mode'] = 'HTML'
            di['photo'] = content['imgList'][0]
            re = self._request('sendPhoto', 'post', json=di)
        elif getListCount(content, 'imgList') == 0 and getListCount(content, 'videoList') == 1:
            di['caption'] = text.tostr()
            di['parse_mode'] = 'HTML'
            di['video'] = content['videoList'][0]['src']
            if 'poster' in content['videoList'][0] and content['videoList'][0]['poster'] is not None and content['videoList'][0]['poster'] != '':
                di['thumb'] = content['videoList'][0]['poster']
            di['supports_streaming'] = True
            re = self._request('sendVideo', 'post', json=di)
        else:
            ind = 0
            di['media'] = []
            for i in content['imgList']:
                di2 = {'type': 'photo', 'media': i}
                if ind == 0:
                    di2['caption'] = text.tostr()
                    di2['parse_mode'] = 'HTML'
                di['media'].append(di2)
                ind = ind + 1
            for i in content['videoList']:
                di2 = {'type': 'video',
                       'media': i['src'], 'supports_streaming': True}
                if 'poster' in i and i['poster'] is not None and i['poster'] != '':
                    di2['thumb'] = i['poster']
                if ind == 0:
                    di2['caption'] = text.tostr()
                    di2['parse_mode'] = 'HTML'
                di['media'].append(di2)
                ind = ind + 1
            re = self._request('sendMediaGroup', 'post', json=di)
        if re is not None and 'ok' in re and re['ok']:
            return True
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
        self._db = database()
        if not exists('settings.txt'):
            print('找不到settings.txt')
            return -1
        self._setting = settings('settings.txt')
        if self._setting._token is None:
            print('没有机器人token')
            return -1
        self._r = Session()
        self._me = self._request('getMe')
        print(self._me)
        if self._me is None:
            print('无法读取机器人信息')
        self._upi = None
        self._updateThread = updateThread(self)
        self._updateThread.start()


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
        self._messageId = self._data['message_id']
        self._chatId = self.__getChatId()
        if self._chatId is None:
            print('未知的chat id')
            return -1
        self._botCommand = None
        if 'text' in self._data:
            if 'entities' in self._data:
                self._botCommand = self.__getBotCommand()
        if self._botCommand is None or self._botCommand not in ['/help', '/rss']:
            self._botCommand = '/help'
        di = {'chat_id': self._chatId}
        self._fromUserId = self.__getFromUserId()
        if self.__getChatType() in ['supergroup', 'group'] and self._fromUserId is not None:
            di['reply_to_message_id'] = self._messageId
        if self._botCommand == '/help':
            di['text'] = '''/help   显示帮助
/rss url    订阅RSS'''
        elif self._botCommand == '/rss':
            self._botCommandPara = self._getCommandlinePara()
            self._uri = None
            for i in self._botCommandPara:
                if i.find('://') > -1:
                    self._uri = i
                    break
            if self._uri is None:
                di['text'] = '没有找到URL'
            else:
                di['text'] = '正在获取信息中……'
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
                self._hash = md5WithBase64(
                    f'{self._uri},{self._messageId},{self._chatId}')
                di['text'] = getMediaInfo(media)
                di['parse_mode'] = 'HTML'
                di['disable_web_page_preview'] = True
                di['reply_markup'] = getInlineKeyBoardWhenRSS(
                    self._hash, media)
                self._main._rssMetaList.addRSSMeta(rssMetaInfo(
                    re['message_id'], media, p.itemList, self._hash))
            self._main._request('editMessageText', 'post', json=di)


class callbackQueryHandle(Thread):
    def __init__(self, main: main, data: dict):
        Thread.__init__(self)
        self._main = main
        self._data = data

    def answer(self, text: str):
        di = {}
        di['callback_query_id'] = self._callbackQueryId
        di['text'] = text
        self._main._request('answerCallbackQuery', 'post', json=di)

    def run(self):
        self._callbackQueryId = self._data['id']
        l = self._data['data'].split(',', 3)
        if len(l) != 3:
            self.answer('错误的按钮数据。')
            return
        try:
            self._loc = int(l[0])
            self._hashd = l[1]
            self._command = int(l[2])
        except:
            self.answer('错误的按钮数据。')
            return
        if self._loc == 0:
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
            self._userId = None
            if 'userId' in self._rssMeta.meta and self._rssMeta.meta['userId'] is not None:
                self._userId = self._rssMeta.meta['userId']
            if self._userId is not None and self._data['from']['id'] != self._userId:
                self.answer('你没有权限操作。')
            if self._inlineKeyBoardCommand == InlineKeyBoardCallBack.SendPriview:
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
                suc = self._main._sendMessage(
                    chatId, self._rssMeta.meta, self._rssMeta.itemList[ran], self._rssMeta.config)
                if suc:
                    self.answer(f'第{ran}条发送成功！')
                else:
                    self.answer(f'第{ran}条发送失败！')
                return
            elif self._userId is not None and self._inlineKeyBoardCommand == InlineKeyBoardCallBack.ModifyChatId:
                self._main._db.setUserStatus(self._userId, userStatus.needInputChatId, self._hashd)
                di = {}
                if 'message' in self._data and self._data['message'] is not None:
                    di['chat_id'] = self._data['message']['chat']['id']
                else:
                    di['chat_id'] = self._data['from']['id']
                di["text"] = "请输入群/频道的ID"
                self._main._request("sendMessage", "post", json=di)
                return
        else:
            self.answer('未知的按钮。')
            return


if __name__ == "__main__":
    m = main()
    m.start()
