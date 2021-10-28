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


class RSSConfig:
    def __init__(self, d: dict = None):
        self.disable_web_page_preview = False
        self.show_RSS_title = True
        self.show_Content_title = True
        self.show_content = True
        self.send_media = True
        self.display_entry_link = False
        if d is not None:
            for k in d.keys():
                if hasattr(self, k):
                    setattr(self, k, d[k])

    def toJson(self):
        return dumps({'disable_web_page_preview': self.disable_web_page_preview, 'show_RSS_title': self.show_RSS_title, 'show_Content_title': self.show_Content_title, 'show_content': self.show_content, 'send_media': self.send_media, 'display_entry_link': self.display_entry_link}, ensure_ascii=False)
