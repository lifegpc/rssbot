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
from html import escape, unescape
import sys
import requests
from traceback import format_exc
from urllib.parse import urljoin


class HTMLSimpleParser(HTMLParser):
    def __init__(self, baseUrl: str=None):
        self.data = ''
        self.istag = False
        self.tagContent = ''
        self.tagAttrs = ''
        self.imgList = []
        self.videoList = []
        self.baseUrl = ''
        if baseUrl is not None:
            self.baseUrl = baseUrl
        HTMLParser.__init__(self)

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.data = self.data + '\n'

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.data = self.data + '\n'
            return
        elif tag == 'img':
            for key, value in attrs:
                if key == 'src':
                    self.imgList.append(urljoin(self.baseUrl, value))
                    break
            return
        elif tag == 'video':
            p = {}
            for key, value in attrs:
                if key == 'src':
                    p['src'] = urljoin(self.baseUrl, value)
                if key == 'poster':
                    p['poster'] = urljoin(self.baseUrl, value)
            if 'src' in p:
                self.videoList.append(p)
            return
        self.istag = True
        self.tagContent = ''
        self.tagAttrs = ''
        if tag == 'a':
            for key, value in attrs:
                if key == 'href':
                    self.tagAttrs = f'{self.tagAttrs} href="{urljoin(self.baseUrl, value)}"'

    def handle_data(self, data):
        if self.istag:
            self.tagContent = self.tagContent + data
        else:
            self.data = self.data + escape(data)

    def handle_endtag(self, tag):
        self.istag = False
        if tag in ['a', 'b', 'i', 'u', 's', 'strong', 'em', 'ins', 'strike', 'del', 'code', 'pre']:
            self.data = f"{self.data}<{tag}{self.tagAttrs}>{escape(self.tagContent)}</{tag}>"
        elif tag not in ['img', 'video', 'br']:
            self.data = f"{self.data}{escape(self.tagContent)}"
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
                typ = 'text/html'
                if 'type' in i.attributes:
                    typ = i.attributes['type'].nodeValue
                if 'href' in i.attributes and typ == 'text/html':
                    m[i.nodeName] = i.attributes['href'].nodeValue
            elif i.nodeName == 'author':
                for k in i.childNodes:
                    if k.nodeName == 'name':
                        m['author'] = k.nodeValue
                        break
                    elif len(k.childNodes) == 1 and k.firstChild.nodeName == '#cdata-section':
                        m['author'] = k.firstChild.nodeValue
                        break
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

    def __checkasrss2(self):
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
        self._type = 'rss2.0'
        return True

    def __dealItem(self, node):
        m = {}
        for i in node.childNodes:
            if i.nodeName == 'link':
                if len(i.childNodes) == 0:
                    m[i.nodeName] = i.nodeValue
                else:
                    m[i.nodeName] = ''
                    for k in i.childNodes:
                        m[i.nodeName] = m[i.nodeName] + k.toxml()
                break
        for i in node.childNodes:
            if i.nodeName == 'link':
                continue
            elif len(i.childNodes) == 0:
                m[i.nodeName] = i.nodeValue
            elif len(i.childNodes) == 1 and i.firstChild.nodeName == '#cdata-section':
                p = HTMLSimpleParser()
                if 'link' in m and m['link'] is not None:
                    p.baseUrl = m['link']
                p.feed(i.firstChild.nodeValue)
                if p.data == '' and i.firstChild.nodeValue.find('<') == -1:
                    m[i.nodeName] = i.firstChild.nodeValue
                else:
                    m[i.nodeName] = p.data
                if i.nodeName in ['description', 'content:encoded']:
                    if i.nodeName == 'content:encoded':
                        m['description'] = m['content:encoded']
                        del m['content:encoded']
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
            if i.nodeName == 'link':
                if 'href' in i.attributes:
                    m[i.nodeName] = i.attributes['href'].nodeValue
        for i in node.childNodes:
            if i.nodeName == 'author':
                for k in i.childNodes:
                    if k.nodeName == 'name':
                        if k.nodeValue is not None:
                            m['author'] = k.nodeValue
                            break
                        elif len(k.childNodes) == 1 and k.firstChild.nodeName == '#cdata-section':
                            m['author'] = k.firstChild.nodeValue
                            break
            elif i.nodeName == 'link':
                continue
            elif i.nodeName in ['title', 'content', 'summary']:
                typ = 'text'
                if 'type' in i.attributes:
                    if i.attributes['type'].nodeValue in ['text', 'html', 'xhtml']:
                        typ = i.attributes['type'].nodeValue
                if len(i.childNodes) == 1 and i.firstChild.nodeName == '#cdata-section':
                    p = HTMLSimpleParser()
                    if 'link' in m and m['link'] is not None:
                        p.baseUrl = m['link']
                    p.feed(i.firstChild.nodeValue)
                    if p.data == '' and i.firstChild.nodeValue.find('<') == -1:
                        m[i.nodeName] = i.firstChild.nodeValue
                    else:
                        m[i.nodeName] = p.data
                    if i.nodeName in ['content', 'summary']:
                        m['imgList'] = p.imgList
                        m['videoList'] = p.videoList
                        m['description'] = m[i.nodeName]
                        del m[i.nodeName]
                elif i.nodeValue is None and len(i.childNodes) == 0:
                    continue
                elif typ == 'text':
                    s = ''
                    if i.nodeValue is not None:
                        s = i.nodeValue
                    else:
                        for k in i.childNodes:
                            s = s + k.toxml()
                    m[i.nodeName] = s
                elif typ == 'html':
                    s = ''
                    if i.nodeValue is not None:
                        s = i.nodeValue
                    else:
                        for k in i.childNodes:
                            s = s + k.toxml()
                    p = HTMLSimpleParser()
                    if 'link' in m and m['link'] is not None:
                        p.baseUrl = m['link']
                    p.feed(s)
                    if p.data == '' and i.firstChild.nodeValue.find('<') == -1:
                        m[i.nodeName] = i.firstChild.nodeValue
                    else:
                        m[i.nodeName] = p.data
                    if i.nodeName in ['content', 'summary']:
                        m['imgList'] = p.imgList
                        m['videoList'] = p.videoList
                        m['description'] = m[i.nodeName]
                        del m[i.nodeName]
                elif typ == 'xhtml':
                    p = HTMLSimpleParser()
                    if 'link' in m and m['link'] is not None:
                        p.baseUrl = m['link']
                    p.feed(i.firstChild.toxml())
                    if p.data == '' and i.firstChild.nodeValue.find('<') == -1:
                        m[i.nodeName] = i.firstChild.nodeValue
                    else:
                        m[i.nodeName] = p.data
                    if i.nodeName in ['content', 'summary']:
                        m['imgList'] = p.imgList
                        m['videoList'] = p.videoList
                        m['description'] = m[i.nodeName]
                        del m[i.nodeName]
            elif len(i.childNodes) == 0:
                m[i.nodeName] = i.nodeValue
            elif len(i.childNodes) == 1 and i.firstChild.nodeName == '#cdata-section':
                p = HTMLSimpleParser()
                if 'link' in m and m['link'] is not None:
                    p.baseUrl = m['link']
                p.feed(i.firstChild.nodeValue)
                if p.data == '' and i.firstChild.nodeValue.find('<') == -1:
                    m[i.nodeName] = i.firstChild.nodeValue
                else:
                    m[i.nodeName] = p.data
            else:
                m[i.nodeName] = ''
                for k in i.childNodes:
                    m[i.nodeName] = m[i.nodeName] + k.toxml()
        return m

    def check(self):
        for f in [self.__checkasrss2, self.__checkasratom]:
            try:
                if f():
                    self.m['_type'] = self._type
                    return True
            except:
                print(format_exc())
                pass
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
        if p.check():
            print(p._type)
        else:
            print('解析失败')
