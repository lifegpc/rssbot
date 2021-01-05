from xml.dom import minidom
import sys
import requests


class RSSParser:
    def __init__(self):
        pass

    def check(self):
        self._root = self.xmldoc.documentElement
        if self._root.localName != 'rss' or len(self._root.childNodes) != 1:
            return False
        self._root2 = self._root.childNodes[0]
        if self._root2.localName != 'channel':
            return False
        m = {}
        for i in self._root2.childNodes:
            if i.localName == 'item':
                pass
            else:
                m[i.localName] = i.firstChild.nodeValue if len(
                    i.childNodes) > 0 else i.nodeValue
        print()

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
