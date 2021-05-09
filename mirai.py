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


class LoginRequiredError(Exception):
    def __init__(self):
        Exception.__init__(self, 'Login is needed.')


def login_required(f):
    @wraps(f)
    def o(*l, **k):
        m: Mirai = l[0]
        if m._logined:
            db: MiraiDatabase = m._db
            v = f(*l, **k)
            if v is not None:
                if v['code'] > 0 and v['code'] <= 4:
                    db.removeSession(m._kses.sessionId)
                    m._logined = False
                    m.login()
                    return o(*l, **k)
            m._kses.lastedUsedTime = m._lastRequestTime
            db.setSession(m._kses)
            return v
        else:
            raise LoginRequiredError()
    return o


class Mirai:
    def __init__(self, m):
        from rssbot import main
        self._m: main = m
        self._db = self._m._mriaidb
        self._ses = Session()
        self._lastRequestTime = 0
        self._logined = False
        self.login()

    def _auth(self, authKey: str):
        r = self._post("/auth", {"authKey": authKey})
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

    def _get(self, path: str, data: dict = None):
        try:
            url = f"{self._m._setting.miraiApiHTTPServer}{path}"
            p = '' if data is None else urlencode(json2data(data))
            if p != '':
                url += '?' + p
            r = self._ses.get(url)
            self._lastRequestTime = time_ns()
            return r
        except:
            return None

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
                r = self._ses.post(url, data=dumps(json, ensure_ascii=False,
                                   separators=(',', ':')))
            else:
                r = self._ses.post(url, data=json2data(json), files=files)
            self._lastRequestTime = time_ns()
            return r
        except:
            return None

    def _release(self, sessionKey: str, qq: int):
        r = self._post("/release", {"sessionKey": sessionKey, "qq": qq})
        if r is None:
            return None
        return r.json()

    def _verify(self, sessionKey: str, qq: int):
        r = self._post("/verify", {"sessionKey": sessionKey, "qq": qq})
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
    def peekMessage(self, count: int = 10):
        "获取bot接收到的最老消息和最老各类事件(不会从MiraiApiHttp消息记录中删除)"
        return self._peekMessage(self._kses.sessionId, count)
