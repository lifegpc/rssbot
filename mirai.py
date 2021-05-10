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
from requests import Session
from dictdeal import json2data
from urllib.parse import urlencode
from json import dumps
from time import time_ns
from miraiDatabase import MiraiSession, MiraiDatabase
from functools import wraps
from typing import Tuple, Union, List


IMG_TYPE = Tuple[str, bytes]
FILE_TYPE = Tuple[str, Union[str, bytes]]


class LoginRequiredError(Exception):
    def __init__(self):
        Exception.__init__(self, 'Login is needed.')


class AlreadyDepreated(Exception):
    def __init__(self, name: str):
        Exception.__init__(self, f'{name} is already depreated.')


def login_required(f):
    @wraps(f)
    def o(*l, **k):
        while True:
            m: Mirai = l[0]
            if m._logined:
                db: MiraiDatabase = m._db
                v = f(*l, **k)
                if v is not None and isinstance(v, dict) and 'code' in v:
                    if v['code'] > 0 and v['code'] <= 4:
                        db.removeSession(m._kses.sessionId)
                        m._logined = False
                        m.login()
                        continue
                m._kses.lastedUsedTime = m._lastRequestTime
                db.setSession(m._kses)
                return v
            else:
                raise LoginRequiredError()
    return o


def version_needed(v: List[int]):
    def i(f):
        @wraps(f)
        def o(*l, **k):
            m: Mirai = l[0]
            if m._version < v:
                return None
            return f(*l, **k)
        return o
    return i


def depreated_at(v: List[int], raise_error: bool = True):
    def i(f):
        @wraps(f)
        def o(*l, **k):
            m: Mirai = l[0]
            if m._version >= v:
                if raise_error:
                    raise AlreadyDepreated(f.__name__)
                return None
            return f(*l, **k)
        return o
    return i


def admin_needed(ind=1):
    "ind: 第i+1个参数是groupId"
    def i(f):
        @wraps(f)
        def o(*l, **k):
            m: Mirai = l[0]
            groupId = l[ind]
            r = m.groupList()
            if r is None or not isinstance(r, list):
                return None
            matched = False
            for n in r:
                if n['id'] == groupId:
                    matched = True
                    if n['permission'] == 'MEMBER':
                        return None
                    break
            if not matched:
                return None
            return f(*l, **k)
        return o
    return i


class Mirai:
    def __init__(self, m):
        from rssbot import main
        self._m: main = m
        self._db = self._m._mriaidb
        self._ses = Session()
        self._ses.headers.update({"Accept-Encoding": "gzip, deflate, br"})
        self._lastRequestTime = 0
        self._logined = False
        self._version = []
        abt = self.about()
        if abt is None or 'code' not in abt or abt['code'] != 0:
            if self._m._setting.miraiApiHTTPVer is None:
                raise ValueError('Unknown Version.')
            ver = self._m._setting.miraiApiHTTPVer
        else:
            ver = abt['data']['version']
        for i in ver.split('-')[0].split('.'):
            self._version.append(int(i))
        if self._version < [1, 10, 0]:
            raise ValueError('mirai-api-http的版本至少为1.10.0')
        self.login()

    def _auth(self, authKey: str):
        path = "/auth" if self._version < [2, 0] else '/verify'
        keyname = "authKey" if self._version < [2, 0] else 'verifyKey'
        r = self._post(path, {keyname: authKey})
        if r is None:
            return None
        return r.json()

    def _countMessage(self, sessionKey: str):
        r = self._get("/countMessage", {"sessionKey": sessionKey})
        if r is None:
            return None
        return r.json()

    def _fetchLatestMessage(self, sessionKey: str, count: int):
        r = self._get("/fetchLatestMessage",
                      {"sessionKey": sessionKey, "count": count})
        if r is None:
            return None
        return r.json()

    def _fetchMessage(self, sessionKey: str, count: int):
        r = self._get("/fetchMessage",
                      {"sessionKey": sessionKey, "count": count})
        if r is None:
            return None
        return r.json()

    def _friendList(self, sessionKey: str):
        r = self._get("/friendList", {"sessionKey": sessionKey})
        if r is None:
            return None
        return r.json()

    def _get(self, path: str, data: dict = None):
        try:
            url = f"{self._m._setting.miraiApiHTTPServer}{path}"
            p = '' if data is None else urlencode(json2data(data))
            if p != '':
                url += '?' + p
            r = self._ses.get(url)
            self._lastRequestTime = time_ns()
            if r.status_code >= 400:
                return None
            return r
        except:
            return None

    def _groupFileInfo(self, sessionKey: str, group: int, id: str):
        r = self._get("/groupFileInfo", {"sessionKey": sessionKey,
                                         "target": group, "id": id})
        if r is None:
            return None
        return r.json()

    def _groupFileList(self, sessionKey: str, group: int, dir: str = None):
        d = {"sessionKey": sessionKey, "target": group}
        if dir is not None:
            d['dir'] = dir
        r = self._get("/groupFileList", d)
        if r is None:
            return None
        return r.json()

    def _groupFileRename(self, sessionKey: str, group: int, id: str,
                         rename: str):
        r = self._post("/groupFileRename", {"sessionKey": sessionKey, "target":
                                            group, "id": id, "rename": rename})
        if r is None:
            return None
        return r.json()

    def _groupList(self, sessionKey: str):
        r = self._get("/groupList", {"sessionKey": sessionKey})
        if r is None:
            return None
        return r.json()

    def _groupMkdir(self, sessionKey: str, group: int, dir: str):
        r = self._post("/groupMkdir", {"sessionKey": sessionKey,
                                       "group": group, "dir": dir})
        if r is None:
            return None
        return r.json()

    def _memberList(self, sessionKey: str, groupId: int):
        r = self._get("/memberList",
                      {"sessionKey": sessionKey, "target": groupId})
        if r is None:
            return None
        return r.json()

    def _messageFromId(self, sessionKey: str, id: int):
        r = self._get("/messageFromId", {"sessionKey": sessionKey, "id": id})
        if r is None:
            return None
        return r.json()

    def _peekLatestMessage(self, sessionKey: str, count: int):
        r = self._get("/peekLatestMessage",
                      {"sessionKey": sessionKey, "count": count})
        if r is None:
            return None
        return r.json()

    def _peekMessage(self, sessionKey: str, count: int):
        r = self._get("/peekMessage",
                      {"sessionKey": sessionKey, "count": count})
        if r is None:
            return None
        return r.json()

    def _post(self, path: str, json: dict, files: dict = None):
        try:
            url = f"{self._m._setting.miraiApiHTTPServer}{path}"
            if files is None:
                r = self._ses.post(url, data=dumps(
                    json, ensure_ascii=False, separators=(',', ':')).encode())
            else:
                r = self._ses.post(url, data=json2data(json), files=files)
            self._lastRequestTime = time_ns()
            if r.status_code > 400:
                if len(r.content) != 0:
                    return r
                return None
            return r
        except:
            return None

    def _recall(self, sessionKey: str, messageId: int):
        r = self._post("/recall",
                       {"sessionKey": sessionKey, "target": messageId})
        if r is None:
            return None
        return r.json()

    def _release(self, sessionKey: str, qq: int):
        r = self._post("/release", {"sessionKey": sessionKey, "qq": qq})
        if r is None:
            return None
        return r.json()

    def _sendFriendMessage(self, sessionKey: str, qq: int, message: list):
        r = self._post("/sendFriendMessage",
                       {"sessionKey": sessionKey, "target": qq,
                        "messageChain": message})
        if r is None:
            return None
        return r.json()

    def _sendGroupMessage(self, sessionKey: str, group: int, message: list):
        r = self._post("/sendGroupMessage",
                       {"sessionKey": sessionKey, "target": group,
                        "messageChain": message})
        if r is None:
            return None
        return r.json()

    def _sendTempMessage(self, sessionKey: str, qq: int, group: int,
                         message: list):
        r = self._post("/sendTempMessage",
                       {"sessionKey": sessionKey, "qq": qq, "group": group,
                        "messageChain": message})
        if r is None:
            return None
        return r.json()

    def _uploadGroupFileAndSend(self, sessionKey: str, groupId: int, path: str,
                                file: FILE_TYPE):
        r = self._post("/uploadFileAndSend",
                       {"sessionKey": sessionKey, "type": "Group", "target": groupId,
                        "path": path}, {"file": file})
        if r is None:
            return None
        return r.json()

    def _uploadImage(self, sessionKey: str, type: str, img: IMG_TYPE):
        r = self._post("/uploadImage",
                       {"sessionKey": sessionKey, "type": type}, {"img": img})
        if r is None:
            return None
        return r.json()

    def _verify(self, sessionKey: str, qq: int):
        path = "/verify" if self._version < [2, 0] else '/bind'
        r = self._post(path, {"sessionKey": sessionKey, "qq": qq})
        if r is None:
            return None
        return r.json()

    def about(self):
        r = self._get("/about")
        if r is None:
            return None
        return r.json()

    @login_required
    def countMessage(self):
        "获取bot接收并缓存的消息总数，注意不包含被删除的"
        return self._countMessage(self._kses.sessionId)

    @login_required
    def fetchLatestMessage(self, count: int = 10):
        "获取bot接收到的最新消息和最新各类事件(会从MiraiApiHttp消息记录中删除)"
        return self._fetchLatestMessage(self._kses.sessionId, count)

    @login_required
    def fetchMessage(self, count: int = 10):
        "获取bot接收到的最老消息和最老各类事件(会从MiraiApiHttp消息记录中删除)"
        return self._fetchMessage(self._kses.sessionId, count)

    @login_required
    def friendList(self):
        "获取bot的好友列表"
        return self._friendList(self._kses.sessionId)

    @login_required
    @version_needed([1, 11, 0])
    def groupFileInfo(self, group: int, id: str):
        "获取群文件详细信息"
        return self._groupFileInfo(self._kses.sessionId, group, id)

    @login_required
    @version_needed([1, 11, 0])
    def groupFileList(self, group: int, dir: str = None):
        "获取群文件列表"
        return self._groupFileList(self._kses.sessionId, group, dir)

    @login_required
    @version_needed([1, 11, 0])
    @admin_needed()
    def groupFileRename(self, group: int, id: str, rename: str):
        "重命名群文件/目录"
        return self._groupFileRename(self._kses.sessionId, group, id, rename)

    @login_required
    def groupList(self):
        "获取bot的群列表"
        return self._groupList(self._kses.sessionId)

    @login_required
    @version_needed([1, 11, 4])
    def groupMkdir(self, group: int, dir: str):
        "创建群文件目录"
        return self._groupMkdir(self._kses.sessionId, group, dir)

    def login(self):
        ses = self._db.getVerifedSession()
        while ses is not None:
            r = self._countMessage(ses.sessionId)
            if r is not None and r['code'] == 0:
                self._kses = ses
                ses.lastedUsedTime = self._lastRequestTime
                self._db.setSession(ses)
                self._logined = True
                return True
            else:
                self._db.removeSession(ses.sessionId)
            ses = self._db.getVerifedSession()
        r = self._auth(self._m._setting.miraiApiHTTPAuthKey)
        if r is None or r['code'] != 0:
            return False
        ses = MiraiSession(r['session'])
        self._db.setSession(ses)
        self._kses = ses
        r = self._verify(ses.sessionId, self._m._setting.miraiApiQQ)
        if r is None or r['code'] != 0:
            self._db.removeSession(ses.sessionId)
            return False
        ses.qq = self._m._setting.miraiApiQQ
        ses.lastedUsedTime = self._lastRequestTime
        ses.status = 1
        self._db.setSession(ses)
        self._logined = True
        return True

    @login_required
    def memberList(self, groupId: int):
        "获取bot指定群中的成员列表"
        return self._memberList(self._kses.sessionId, groupId)

    @login_required
    def messageFromId(self, id: int):
        "获取bot接收到的消息和各类事件"
        return self._messageFromId(self._kses.sessionId, id)

    @login_required
    def peekLatestMessage(self, count: int = 10):
        "获取bot接收到的最新消息和最新各类事件(不会从MiraiApiHttp消息记录中删除)"
        return self._peekLatestMessage(self._kses.sessionId, count)

    @login_required
    def peekMessage(self, count: int = 10):
        "获取bot接收到的最老消息和最老各类事件(不会从MiraiApiHttp消息记录中删除)"
        return self._peekMessage(self._kses.sessionId, count)

    @login_required
    def recall(self, messageId: int):
        """撤回指定消息。
        对于bot发送的消息，有2分钟时间限制。
        对于撤回群聊中群员的消息，需要有相应权限"""
        return self._recall(self._kses.sessionId, messageId)

    def release(self):
        if self._logined:
            r = self._release(self._kses.sessionId,
                              self._m._setting.miraiApiQQ)
            if r is None:
                return
            self._logined = False
            self._db.removeSession(self._kses.sessionId)

    @login_required
    def sendFriendMessage(self, qq: int, message: list):
        "向指定好友发送消息"
        return self._sendFriendMessage(self._kses.sessionId, qq, message)

    @login_required
    def sendGroupMessage(self, group: int, message: list):
        "向指定群发送消息"
        return self._sendGroupMessage(self._kses.sessionId, group, message)

    @login_required
    def sendTempMessage(self, qq: int, group: int, message: list):
        "向临时会话对象发送消息"
        return self._sendTempMessage(self._kses.sessionId, qq, group, message)

    @login_required
    def uploadFriendImage(self, img: IMG_TYPE):
        "上传图片文件至服务器并返回ImageId（好友图片）"
        return self._uploadImage(self._kses.sessionId, "friend", img)

    @login_required
    @version_needed([1, 11, 0])
    @admin_needed()
    def uploadGroupFileAndSend(self, groupId: int, path: str, file: FILE_TYPE):
        "上传文件至群并返回FileId（测试需要管理员权限）"
        return self._uploadGroupFileAndSend(self._kses.sessionId, groupId,
                                            path, file)

    @login_required
    def uploadGroupImage(self, img: IMG_TYPE):
        "上传图片文件至服务器并返回ImageId（群图片）"
        return self._uploadImage(self._kses.sessionId, "group", img)

    @login_required
    def uploadTempImage(self, img: IMG_TYPE):
        "上传图片文件至服务器并返回ImageId（临时图片）"
        return self._uploadImage(self._kses.sessionId, "temp", img)
