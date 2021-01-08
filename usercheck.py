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
from enum import Enum, unique


@unique
class UserPermissionsInChatCheckResult(Enum):
    OK = 0
    GetChatInfoError = 1
    PrivateChat = 2
    GetChatAdministratorsError = 3
    NoPermissions = 4


def checkUserPermissionsInChat(m, chatId: int, userId: int) -> UserPermissionsInChatCheckResult:
    from rssbot import main
    _main: main = m
    re = _main._request('getChat', 'post', {'chat_id': chatId})
    if re is None or 'ok' not in re or not re['ok']:
        return UserPermissionsInChatCheckResult.GetChatInfoError
    chatInfo = re['result']
    if chatInfo['type'] == 'private':
        return UserPermissionsInChatCheckResult.PrivateChat
    re = _main._request('getChatAdministrators', 'post', {'chat_id': chatId})
    if re is None or 'ok' not in re or not re['ok']:
        return UserPermissionsInChatCheckResult.GetChatAdministratorsError
    chatAdministrators = re['result']
    for chatMember in chatAdministrators:
        if chatMember['user']['id'] != userId:
            continue
        if chatMember['status'] not in ['creator', 'administrator']:
            continue
        if chatInfo['type'] == 'channel' and chatMember['status'] == 'administrator' and ('can_post_messages' not in chatMember or not chatMember['can_post_messages']):
            continue
        if chatInfo['type'] == 'channel' and chatMember['status'] == 'administrator' and ('can_edit_messages' not in chatMember or not chatMember['can_edit_messages']):
            continue
        return UserPermissionsInChatCheckResult.OK
    return UserPermissionsInChatCheckResult.NoPermissions
