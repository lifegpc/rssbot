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
from xml.dom import minidom
from html.parser import HTMLParser
from html import escape
import sys
import requests
from traceback import format_exc


class HTMLSimpleParser(HTMLParser):
    def __init__(self):
        self.data = ''
        self.istag = False
        self.tagContent = ''
        self.tagAttrs = ''
        self.imgList = []
        self.videoList = []
        HTMLParser.__init__(self)

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            data = data + '\n'

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.data = self.data + '\n'
            return
        elif tag == 'img':
            for key, value in attrs:
                if key == 'src':
                    self.imgList.append(value)
                    break
            return
        elif tag == 'video':
            p = {}
            for key, value in attrs:
                if key == 'src':
                    p['src'] = value
                if key == 'poster':
                    p['poster'] = value
            if 'src' in p:
                self.videoList.append(p)
            return
        self.istag = True
        self.tagContent = ''
        self.tagAttrs = ''
        if tag == 'a':
            for key, value in attrs:
                if key == 'href':
                    self.tagAttrs = f'{self.tagAttrs} href="{value}"'

    def handle_data(self, data):
        if self.istag:
            self.tagContent = self.tagContent + data
        else:
            self.data = self.data + data

    def handle_endtag(self, tag):
        self.istag = False
        if tag in ['a', 'b', 'i', 'u', 's', 'strong', 'em', 'ins', 'strike', 'del', 'code', 'pre']:
            self.data = f"{self.data}<{tag}{self.tagAttrs}>{self.tagContent}</{tag}>"
        self.tagAttrs = ''


class RSSParser:
    def __init__(self):
        pass

    def __checkasratom(self):
        self._root = self.xmldoc.documentElement
        if self._root.nodeName != 'feed':
            return False
        m = {}
        itemList = []
        for i in self._root.childNodes:
            if i.nodeName == 'entry':
                itemList.append(self.__dealItemAtom(i))
            elif i.nodeName == 'link':
                if 'href' in i.attributes:
                    m[i.nodeName] = i.attributes['href'].nodeValue
            elif i.nodeName == 'author':
                if len(i.childNodes) == 1 and i.firstChild.nodeName == 'name':
                    name = i.firstChild
                    if len(name.childNodes) == 1 and name.firstChild.nodeName == '#cdata-section':
                        m['author'] = name.firstChild.nodeValue
            else:
                if len(i.childNodes) == 0:
                    m[i.nodeName] = i.nodeValue
                elif len(i.childNodes) == 1 and i.firstChild.nodeName == '#cdata-section':
                    m[i.nodeName] = i.firstChild.nodeValue
                else:
                    m[i.nodeName] = ''
                    for k in i.childNodes:
                        m[i.nodeName] = m[i.nodeName] + k.toxml()
        if 'title' not in m or m['title'] is None or m['title'] == '':
            return False
        self.m = m
        self.title = m['title']
        self.ttl = None
        self.itemList = itemList
        self._type = 'atom'
        return True

    def __checkasrss3(self):
        self._root = self.xmldoc.documentElement
        if self._root.localName != 'rss' or len(self._root.childNodes) != 1:
            return False
        self._root2 = self._root.childNodes[0]
        if self._root2.localName != 'channel':
            return False
        m = {}
        itemList = []
        for i in self._root2.childNodes:
            if i.nodeName == 'item':
                itemList.append(self.__dealItem(i))
            elif i.nodeName == 'atom:link':
                if 'href' in i.attributes:
                    m[i.nodeName] = i.attributes['href'].nodeValue
            else:
                if len(i.childNodes) == 0:
                    m[i.nodeName] = i.nodeValue
                elif len(i.childNodes) == 1 and i.firstChild.nodeName == '#cdata-section':
                    m[i.nodeName] = i.firstChild.nodeValue
                else:
                    m[i.nodeName] = ''
                    for k in i.childNodes:
                        m[i.nodeName] = m[i.nodeName] + k.toxml()
        if 'title' not in m or m['title'] is None or m['title'] == '':
            return False
        self.m = m
        self.title = m['title']
        self.ttl = None
        if 'ttl' in m and m['ttl'] is not None and m['ttl'].isnumeric():
            self.ttl = int(m['ttl'])
        self.itemList = itemList
        self._type = 'rss3.0'
        return True

    def __dealItem(self, node):
        m = {}
        for i in node.childNodes:
            if len(i.childNodes) == 0:
                m[i.nodeName] = i.nodeValue
            elif len(i.childNodes) == 1 and i.firstChild.nodeName == '#cdata-section':
                p = HTMLSimpleParser()
                p.feed(i.firstChild.nodeValue)
                if p.data == '' and i.firstChild.nodeValue.find('<') == -1:
                    m[i.nodeName] = i.firstChild.nodeValue
                else:
                    m[i.nodeName] = p.data
                if i.nodeName == 'description':
                    m['imgList'] = p.imgList
                    m['videoList'] = p.videoList
            else:
                m[i.nodeName] = ''
                for k in i.childNodes:
                    m[i.nodeName] = m[i.nodeName] + k.toxml()
        return m

    def __dealItemAtom(self, node):
        m = {}
        for i in node.childNodes:
            if i.nodeName == 'author':
                if len(i.childNodes) == 1 and i.firstChild.nodeName == 'name':
                    name = i.firstChild
                    if len(name.childNodes) == 1 and name.firstChild.nodeName == '#cdata-section':
                        m['author'] = name.firstChild.nodeValue
            elif i.nodeName == 'link':
                if 'href' in i.attributes:
                    m[i.nodeName] = i.attributes['href'].nodeValue
            elif len(i.childNodes) == 0:
                m[i.nodeName] = i.nodeValue
            elif len(i.childNodes) == 1 and i.firstChild.nodeName == '#cdata-section':
                p = HTMLSimpleParser()
                p.feed(i.firstChild.nodeValue)
                if p.data == '' and i.firstChild.nodeValue.find('<') == -1:
                    m[i.nodeName] = i.firstChild.nodeValue
                else:
                    m[i.nodeName] = p.data
                if i.nodeName == 'content':
                    m['imgList'] = p.imgList
                    m['videoList'] = p.videoList
                    m['description'] = m['content']
                    del m['content']
            else:
                m[i.nodeName] = ''
                for k in i.childNodes:
                    m[i.nodeName] = m[i.nodeName] + k.toxml()
        return m

    def check(self):
        try:
            checked = self.__checkasrss3()
            if not checked:
                checked = self.__checkasratom()
            return checked
        except:
            print(format_exc())
            return False

    def normalize(self):
        self.removeblank(self.xmldoc.documentElement)
        self.xmldoc.normalize()

    def parse(self, fn: str):
        try:
            if fn.find('://') > -1:
                re = requests.get(fn)
                if re.status_code == 200:
                    self.xmldoc = minidom.parseString(re.text)
            else:
                self.xmldoc = minidom.parse(fn)
            self.normalize()
            return True
        except:
            return False

    def removeblank(self, node):
        for i in node.childNodes:
            if i.nodeType == minidom.Node.TEXT_NODE:
                if i.nodeValue:
                    i.nodeValue = i.nodeValue.strip()
            elif i.nodeType == minidom.Node.ELEMENT_NODE:
                self.removeblank(i)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fn = sys.argv[1]
        p = RSSParser()
        p.parse(fn)
        p.check()
