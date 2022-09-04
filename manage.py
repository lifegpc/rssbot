# (C) 2021-2022 lifegpc
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
from enum import Enum, unique


@unique
class InlineKeyBoardForManage(Enum):
    Close = 0
    ManageByRSS = 1
    ManageByChatId = 2
    FirstPage = 3


def getInlineKeyBoardForManage():
    d = []
    i = -1
    d.append([])
    i += 1
    d[i].append({'text': '按RSS管理', 'callback_data': f'3,{InlineKeyBoardForManage.ManageByRSS.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '按用户管理', 'callback_data': f'3,{InlineKeyBoardForManage.ManageByChatId.value}'})
    d.append([])
    i += 1
    d[i].append({'text': '关闭', 'callback_data': f'3,{InlineKeyBoardForManage.Close.value}'})
    return {'inline_keyboard': d}
