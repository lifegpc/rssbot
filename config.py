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
from json import dumps
from enum import Enum, unique


@unique
class SendUgoiraMethod(Enum):
    ANIMATION_VIDEO = 0
    ANIMATION_FILE = 1
    VIDEO = 2
    FILE = 3

    def __str__(self) -> str:
        if self._value_ == 0:
            return '动图(太大时视频)'
        elif self._value_ == 1:
            return '动图(太大时文件)'
        elif self._value_ == 2:
            return '视频'
        elif self._value_ == 3:
            return '文件'


class MessageThreadIdList:
    def __init__(self) -> None:
        self._list = []
        self._without_id = False

    def iter(self):
        if len(self._list) == 0:
            return [None]
        li = [None] + self._list if self._without_id else self._list
        return li

    @property
    def isEnabled(self):
        return len(self._list) != 0

    def addId(self, id: int):
        if id not in self._list:
            self._list.append(id)

    def clear(self):
        self._list.clear()
        self._without_id = False

    def removeId(self, id: int):
        if id in self._list:
            self._list.remove(id)
            return True
        return False


class RSSConfig:
    def __init__(self, d: dict = None):
        self.disable_web_page_preview = False
        self.show_RSS_title = True
        self.show_Content_title = True
        self.show_content = True
        self.send_media = True
        self.display_entry_link = False
        self.send_img_as_file = False
        self.send_origin_file_name = False
        self.send_ugoira_with_origin_pix_fmt = False
        self.send_ugoira_method = SendUgoiraMethod(0)
        self.compress_big_image = True
        self.thread_ids = MessageThreadIdList()
        self.add_author = False
        self.interval = None
        self.update(d)

    def toJson(self):
        return dumps({'disable_web_page_preview': self.disable_web_page_preview, 'show_RSS_title': self.show_RSS_title, 'show_Content_title': self.show_Content_title, 'show_content': self.show_content, 'send_media': self.send_media, 'display_entry_link': self.display_entry_link, 'send_img_as_file': self.send_img_as_file, 'send_ugoira_with_origin_pix_fmt': self.send_ugoira_with_origin_pix_fmt, 'send_ugoira_method': self.send_ugoira_method.value, "compress_big_image": self.compress_big_image, 'thread_ids': {'list': self.thread_ids._list, 'without_id': self.thread_ids._without_id}, 'add_author': self.add_author}, ensure_ascii=False)

    def update(self, d: dict):
        if d is not None:
            for k in d.keys():
                if hasattr(self, k):
                    if k == 'send_ugoira_method':
                        self.send_ugoira_method = SendUgoiraMethod(d[k])
                    elif k == 'thread_ids':
                        self.thread_ids._list = d[k]['list']
                        self.thread_ids._without_id = d[k]['without_id']
                    else:
                        setattr(self, k, d[k])

    def toGlobalJson(self):
        return dumps({'send_origin_file_name': self.send_origin_file_name, 'interval': self.interval}, ensure_ascii=False)
