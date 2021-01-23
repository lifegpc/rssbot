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
from time import strftime, localtime, timezone
from urllib.parse import unquote, urlsplit
from html.parser import HTMLParser


class TGHTMLParser(HTMLParser):
    """Only for calculate message's length and cut message.
    Do not send these message entries to Telegram."""

    def __init__(self):
        HTMLParser.__init__(self)
        self.messageEntries = []
        self.s = ''
        self.__tagL = []
        self.__entryL = []

    def close(self):
        """This function will do some check for message entries after close."""
        HTMLParser.close(self)
        for e in self.messageEntries:
            e['dataend'] = e['end']
            e['end'] = e['end'] + len(e['tag']) + 3

    def feed(self, s: str):
        """This function will repelace \\n with &lt;br&gt;.
        Telegram do not support &lt;br&gt; and use \\n."""
        HTMLParser.feed(self, s.replace('\n', '<br>'))

    def handle_data(self, data: str):
        self.s = self.s + data
        if len(self.__entryL) > 0:
            if self.__entryL[-1]['datastart'] == -1:
                self.__entryL[-1]['datastart'] = self.getpos()[1]

    def handle_starttag(self, tag: str, attrs):
        if len(self.__entryL) > 0:
            if self.__entryL[-1]['datastart'] == -1:
                self.__entryL[-1]['datastart'] = self.getpos()[1]
        typ = ''
        if tag in ['b', 'strong']:
            typ = 'bold'
        elif tag in ['i', 'em']:
            typ = 'italic'
        elif tag in ['u', 'ins']:
            typ = 'underline'
        elif tag in ['s', 'strike', 'del']:
            typ = 'strikethrough'
        elif tag in ['a']:
            typ = 'url'
            link = None
            for name, value in attrs:
                if name == 'href':
                    link = value
                    break
        elif tag in ['code', 'pre']:
            typ = tag
        elif tag == 'br':
            self.s = self.s + '\n'
            return
        else:
            return  # unsuppoted tag
        t = {'type': typ, 'offset': len(self.s), 'length': 0, 'tag': tag, 'start': self.getpos()[
            1], 'end': 0, 'datastart': -1}
        if typ == 'url' and link is not None:
            t['url'] = link
        self.__entryL.append(t)
        self.messageEntries.append(t)
        self.__tagL.append(tag)

    def handle_endtag(self, tag: str):
        if len(self.__entryL) > 0:
            if self.__entryL[-1]['datastart'] == -1:
                self.__entryL[-1]['datastart'] = self.getpos()[1]
        if tag not in ['b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'a', 'pre', 'code']:
            return
        if len(self.__tagL) <= 0:
            return
        if self.__entryL[-1]['datastart'] == -1:
            self.__entryL[-1]['datastart'] = self.getpos()[1]
        self.__entryL[-1]['end'] = self.getpos()[1]
        self.__entryL[-1]['length'] = len(self.s) - self.__entryL[-1]['offset']
        self.__entryL = self.__entryL[:-1]
        self.__tagL = self.__tagL[:-1]


class MessageEntries:
    def __init__(self, l: list):
        self.__list = l

    def __len__(self):
        return len(self.__list)

    def getStr(self, l: int, s: str, re: str) -> (str, str):
        """split string
        s is origin string
        re is parsed string"""
        s = s.replace(
            '\n', '<br>')  # the start and end is needed work with <br>
        t = sorted(self.__list, key=lambda d: d['start'])
        r = ''
        i = 0
        while i < l:
            for v in t:
                if v['offset'] == i:
                    r = r + s[v['start']:v['datastart']]
            r = r + re[i]
            for v in reversed(t):
                if v['offset'] + v['length'] - 1 == i:
                    r = r + s[v['dataend']:v['end']]
            i = i + 1
        for v in reversed(t):
            if i - 1 >= v['offset'] and v['offset'] + v['length'] - 1 > i - 1:
                r = r + s[v['dataend']:v['end']]
        r2 = ''
        i = l
        for v in t:
            if i > v['offset'] and v['offset'] + v['length'] - 1 >= i:
                r2 = r2 + s[v['start']:v['datastart']]
        while i < len(re):
            for v in t:
                if v['offset'] == i:
                    r2 = r2 + s[v['start']:v['datastart']]
            r2 = r2 + re[i]
            for v in reversed(t):
                if v['offset'] + v['length'] - 1 == i:
                    r2 = r2 + s[v['dataend']:v['end']]
            i = i + 1
        return r, r2

    def isOkWithOrigin(self, l: int) -> bool:
        for v in self.__list:
            if l > v['start'] and l < v['end']:
                return False
        return True

    def isOkWithRe(self, l: int) -> bool:
        for v in self.__list:
            if l > v['offset'] and l < (v['offset'] + v['length']):
                return False
        return True


class textc:
    def __len__(self):
        p = TGHTMLParser()
        p.feed(self.__str)
        p.close()
        return len(p.s)

    def __init__(self):
        self.__str = ''
        self.__max = 4096

    def __str__(self):
        return self.__str

    def checklen(self):
        return len(self) <= self.__max

    def cut(self):
        """Split string"""
        p = TGHTMLParser()
        p.feed(self.__str)
        p.close()
        m = MessageEntries(p.messageEntries)
        l = self.__str.splitlines(True)
        l2 = p.s.splitlines(True)
        originlen = []  # line's origin length
        rlen = []  # line's length after parsing
        t = ''
        t2 = ''
        z = 0  # calculate the offset because of replace \n with <br>
        for i in range(min(len(l), len(l2))):
            if l[i].endswith('\n'):
                z = z + 1
            t = t + l[i]
            t2 = t2 + l2[i]
            originlen.append(len(t) + 3 * z)
            rlen.append(len(t2))
        for i in reversed(range(len(originlen))):
            if rlen[i] <= self.__max:  # check the length
                # make sure not break HTML
                if m.isOkWithOrigin(originlen[i]) and m.isOkWithRe(rlen[i]):
                    r = ''
                    for k in range(i + 1):
                        r = r + l[k]
                    l = l[i+1:]
                    t = ''
                    for i in l:
                        t = t + i
                    self.__str = t
                    return r
                else:
                    r, self.__str = m.getStr(rlen[i], self.__str, p.s)
                    return r
        r, self.__str = m.getStr(self.__max, self.__str, p.s)
        return r

    def tostr(self, maxLength: int = 4096):
        self.__max = maxLength
        if self.checklen():
            t = self.__str
            self.__str = ''
            return t
        else:
            return self.cut()

    def addtotext(self, s: str):
        if self.__str == '':
            self.__str = f"{self.__str}{s}"
        else:
            self.__str = f'{self.__str}\n{s}'


def timeToStr(t: int) -> str:
    te = strftime('%Y-%m-%dT%H:%M:%S', localtime(t))
    op = '-' if timezone > 0 else '+'
    te = te + op + \
        f'{int(abs(timezone)/3600):02}:{int(abs(timezone)%3600/60):02}'
    return te


def removeEmptyLine(s: str) -> str:
    l = s.splitlines(False)
    r = []
    for v in l:
        if v != '':
            r.append(v)
    f = True
    z = ''
    for v in r:
        if f:
            f = False
            z = v
        else:
            z = z + '\n' + v
    return z


def decodeURI(s: str) -> str:
    s = s.replace('%25', '%2525')
    s = s.replace('%3A', '%253A')
    s = s.replace('%3a', '%253A')
    s = s.replace('%2F', '%252F')
    s = s.replace('%2f', '%252F')
    s = s.replace('%3F', '%253F')
    s = s.replace('%3f', '%253F')
    s = s.replace('%23', '%2523')
    s = s.replace('%5B', '%255B')
    s = s.replace('%5b', '%255B')
    s = s.replace('%5D', '%255D')
    s = s.replace('%5d', '%255D')
    s = s.replace('%40', '%2540')
    s = s.replace('%21', '%2521')
    s = s.replace('%24', '%2524')
    s = s.replace('%26', '%2526')
    s = s.replace('%27', '%2527')
    s = s.replace('%28', '%2528')
    s = s.replace('%29', '%2529')
    s = s.replace('%2A', '%252A')
    s = s.replace('%2a', '%252A')
    s = s.replace('%2B', '%252B')
    s = s.replace('%2b', '%252B')
    s = s.replace('%2C', '%252C')
    s = s.replace('%2c', '%252C')
    s = s.replace('%3B', '%253B')
    s = s.replace('%3b', '%253B')
    s = s.replace('%3D', '%253D')
    s = s.replace('%3d', '%253D')
    s = s.replace('%20', '%2520')
    return unquote(s)
