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
from json import loads
from config import RSSConfig


class ChatEntry:
    def __init__(self, data=None):
        self.chatId = data[0] if data is not None and data[0] is not None else None
        self.id = data[1] if data is not None and data[1] is not None else None
        try:
            self.config = RSSConfig(
                loads(data[2])) if data is not None and data[2] is not None else RSSConfig()
        except:
            self.config = RSSConfig()


class RSSEntry:
    def __init__(self, data=None):
        self.title = None
        if data is not None and data[0] is not None:
            self.title = data[0]
        self.url = None
        if data is not None and data[1] is not None:
            self.url = data[1]
        self.interval = None
        if data is not None and data[2] is not None:
            self.interval = data[2]
        self.lastupdatetime = None
        if data is not None and data[3] is not None:
            self.interval = data[3]
        self.id = None
        if data is not None and data[4] is not None:
            self.id = data[4]
        self.chatList = []
