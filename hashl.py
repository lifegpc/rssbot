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
from hashlib import sha256 as sha256a, md5 as md5a
from base64 import b64encode


def sha256(s) -> str:
    a = sha256a()
    a.update(str(s).encode())
    return a.hexdigest()

def md5(s) -> str:
    a = md5a()
    a.update(str(s).encode())
    return a.hexdigest()

def sha256WithBase64(s) -> str:
    a = sha256a()
    a.update(str(s).encode())
    return b64encode(a.digest()).decode()

def md5WithBase64(s) -> str:
    a = md5a()
    a.update(str(s).encode())
    return b64encode(a.digest()).decode()
