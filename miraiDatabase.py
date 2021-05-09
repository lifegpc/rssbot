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
import sqlite3
from typing import List, Union
from enum import Enum, unique
from threading import Lock
from time import time_ns


SESSION_TABLE = '''CREATE TABLE mirai_session (
sessionId TEXT,
qq INT,
status INT,
lastedUsedTime INT,
PRIMARY KEY (sessionId)
);'''


@unique
class MiraiSessionStatus(Enum):
    CREATED = 0
    VERIFIED = 1
    RELEASED = 2


class MiraiSession:
    def __init__(self, sessionId: str, qq: int = None, status: Union[MiraiSessionStatus, int] = None, lastedUsedTime: int = None):
        self._sessionId = sessionId
        self._qq = qq
        if status is None:
            self._status = MiraiSessionStatus(0)
        elif isinstance(status, MiraiSessionStatus):
            self._status = status
        elif isinstance(status, int) and status >= 0 and status <= 2:
            self._status = MiraiSessionStatus(status)
        else:
            self._status = MiraiSessionStatus(0)
        self._lastedUsedTime = lastedUsedTime

    @property
    def sessionId(self) -> str:
        return self._sessionId

    @property
    def qq(self) -> int:
        if self._qq is None:
            return None
        if isinstance(self._qq, int):
            return self._qq
        else:
            raise ValueError('qq must be int.')

    @qq.setter
    def qq(self, v):
        if isinstance(v, int):
            self._qq = v

    @property
    def status(self) -> MiraiSessionStatus:
        return self._status

    @status.setter
    def status(self, v):
        if isinstance(v, MiraiSessionStatus):
            self._status = v
        elif isinstance(v, int) and v >= 0 and v <= 2:
            self._status = MiraiSessionStatus(v)

    @property
    def lastedUsedTime(self) -> int:
        if self._lastedUsedTime is None:
            return None
        if isinstance(self._lastedUsedTime, int):
            return self._lastedUsedTime
        else:
            raise ValueError('lastedUsedTime must be int.')

    @lastedUsedTime.setter
    def lastedUsedTime(self, v):
        if isinstance(v, int):
            self._lastedUsedTime = v


class MiraiDatabase:
    def __check_database(self):
        self.__updateExistsTable()
        v = self.__read_version()
        if v is None:
            return False
        if v < self._version:
            self.__updateExistsTable()
            self.__write_version()
        return True

    def __create_table(self):
        if 'mirai_session' not in self._exist_tables:
            self._db.execute(SESSION_TABLE)
        self.__write_version()
        self._db.commit()

    def __init__(self, m, loc: str):
        self._version = [1, 0, 0, 0]
        self._lock = Lock()
        self._db = sqlite3.connect(loc, check_same_thread=False)
        ok = self.__check_database()
        if not ok:
            self.__create_table()
        from rssbot import main
        self._main: main = m
        self.removeUselessSession()

    def __write_version(self):
        if self.__read_version() is None:
            self._db.execute('INSERT INTO version VALUES (?, ?, ?, ?, ?);',
                             tuple(['mirai'] + self._version))
        else:
            self._db.execute(
                "UPDATE version SET v1=?, v2=?, v3=?, v4=? WHERE id='mirai';",
                tuple(self._version))
        self._db.commit()

    def __read_version(self) -> List[int]:
        cur = self._db.execute("SELECT * FROM version WHERE id='mirai';")
        for i in cur:
            return [k for k in i if isinstance(k, int)]

    def __updateExistsTable(self):
        cur = self._db.execute('SELECT * FROM main.sqlite_master;')
        self._exist_tables = {}
        for i in cur:
            if i[0] == 'table':
                self._exist_tables[i[1]] = i

    def getSession(self, sessionId: str, checkOnly: bool = False) -> Union[MiraiSession, bool]:
        cur = self._db.execute(
            'SELECT * FROM mirai_session WHERE sessionId=?;', (sessionId,))
        for i in cur:
            if checkOnly:
                return True
            return MiraiSession(*i)
        if checkOnly:
            return False
        return None

    def getVerifedSession(self) -> MiraiSession:
        self.removeUselessSession()
        cur = self._db.execute('SELECT * FROM mirai_session WHERE status=1;')
        for i in cur:
            return MiraiSession(*i)
        return None

    def removeSession(self, sessionId: str):
        if self.getSession(sessionId, True):
            self._db.execute(
                'DELETE FROM mirai_session WHERE sessionId=?;', (sessionId,))
            self._db.commit()

    def removeUselessSession(self):
        with self._lock:
            try:
                self._db.execute(
                    'DELETE FROM mirai_session WHERE status=? OR lastedUsedTime < ?;',
                    (MiraiSessionStatus.RELEASED.value, round(time_ns() - 1.8E12)))
                self._db.commit()
                return True
            except:
                return False

    def setSession(self, ses: MiraiSession):
        if self.getSession(ses.sessionId, True):
            self._db.execute(
                'UPDATE mirai_session SET qq=?, status=?, lastedUsedTime=? WHERE sessionId=?;',
                (ses.qq, ses.status.value, ses.lastedUsedTime, ses.sessionId))
        else:
            self._db.execute('INSERT INTO mirai_session VALUES (?, ?, ?, ?);',
            (ses.sessionId, ses.qq, ses.status.value, ses.lastedUsedTime))
        self._db.commit()
