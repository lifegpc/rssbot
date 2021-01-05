from database import database
from os.path import exists
from readset import settings
from requests import Session
from traceback import format_exc
from threading import Thread


class main:
    def __init__(self):
        pass

    def _request(self, methodName: str, HTTPMethod: str = 'get', data: dict = None, json: dict = None, returnType: str = 'json'):
        try:
            r = self._r.request(
                HTTPMethod, f'https://api.telegram.org/bot{self._setting._token}/{methodName}', data=data, json=json)
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

    def _updateLoop(self):
        d = {'allowed_updates': [
            'message', 'edited_message', 'channel_post', 'edited_channel_post']}
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
    
    def run(self):
        print(self._data)
        self._messageId = self._data['message_id']
        self._chatId = self.__getChatId()
        if self._chatId is None:
            print('未知的chat id')
            return -1
        if 'text' in self._data:
            if 'entities' in self._data:
                self._botCommand = self.__getBotCommand()
        if self._botCommand is None:
            self._botCommand = '/help'
        if self._botCommand not in ['/help']:
            self._botCommand = '/help'
        di = {'chat_id': self._chatId}
        self._fromUserId = self.__getFromUserId()
        if self.__getChatType() in ['supergroup', 'group'] and self._fromUserId is not None:
            di['reply_to_message_id'] = self._messageId
        if self._botCommand == '/help':
            di['text'] = '/help 查看帮助'
        self._main._request('sendMessage', 'post', json=di)


if __name__ == "__main__":
    m = main()
    m.start()
