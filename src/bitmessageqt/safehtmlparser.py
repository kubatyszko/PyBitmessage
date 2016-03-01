from HTMLParser import HTMLParser
import inspect
import re
from urllib import quote, quote_plus
from urlparse import urlparse

class SafeHTMLParser(HTMLParser):
    # from html5lib.sanitiser
    acceptable_elements = ['a', 'abbr', 'acronym', 'address', 'area',
                           'article', 'aside', 'audio', 'b', 'big', 'blockquote', 'br', 'button',
                           'canvas', 'caption', 'center', 'cite', 'code', 'col', 'colgroup',
                           'command', 'datagrid', 'datalist', 'dd', 'del', 'details', 'dfn',
                           'dialog', 'dir', 'div', 'dl', 'dt', 'em', 'event-source', 'fieldset',
                           'figcaption', 'figure', 'footer', 'font', 'header', 'h1',
                           'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'ins',
                           'keygen', 'kbd', 'label', 'legend', 'li', 'm', 'map', 'menu', 'meter',
                           'multicol', 'nav', 'nextid', 'ol', 'output', 'optgroup', 'option',
                           'p', 'pre', 'progress', 'q', 's', 'samp', 'section', 'select',
                           'small', 'sound', 'source', 'spacer', 'span', 'strike', 'strong',
                           'sub', 'sup', 'table', 'tbody', 'td', 'textarea', 'time', 'tfoot',
                           'th', 'thead', 'tr', 'tt', 'u', 'ul', 'var', 'video']
    replaces = [["&", "&amp;"], ["\"", "&quot;"], ["<", "&lt;"], [">", "&gt;"], ["\n", "<br/>"], ["\t", "&nbsp;&nbsp;&nbsp;&nbsp;"], ["  ", "&nbsp; "], ["  ", "&nbsp; "], ["<br/> ", "<br/>&nbsp;"]]
    src_schemes = [ "data" ]
    uriregex1 = re.compile(r'(\b(?:https?|telnet|gopher|file|wais|ftp):[\w/#~:.?+=&%@!\-.:;?\\-]+?(?=[.:?\-]*(?:[^\w/#~:;.?+=&%@!\-.:?\-]|$)))')
    uriregex2 = re.compile(r'<a href="([^"]+)&amp;')
    emailregex = re.compile(r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b')

    @staticmethod
    def multi_replace(text):
        for a in SafeHTMLParser.replaces:
            text = text.replace(a[0], a[1])
        if len(text) > 1 and text[0] == " ":
            text = "&nbsp;" + text[1:]
        return text

    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.reset_safe()
        
    def reset_safe(self):
        self.elements = set()
        self.raw = u""
        self.sanitised = u""
        self.has_html = False
        self.allow_picture = False
        self.allow_external_src = False

    def add_if_acceptable(self, tag, attrs = None):
        if not tag in SafeHTMLParser.acceptable_elements:
            return
        self.sanitised += "<"
        if inspect.stack()[1][3] == "handle_endtag":
            self.sanitised += "/"
        self.sanitised += tag
        if not attrs is None:
            for attr, val in attrs:
                if tag == "img" and attr == "src" and not self.allow_picture:
                    val = ""
                elif attr == "src" and not self.allow_external_src:
                    url = urlparse(val)
                    if url.scheme not in SafeHTMLParser.src_schemes:
                        val == ""
                self.sanitised += " " + quote_plus(attr)
                if not (val is None):
                    self.sanitised += "=\"" + val + "\""
        if inspect.stack()[1][3] == "handle_startendtag":
            self.sanitised += "/"
        self.sanitised += ">"
    
    def handle_starttag(self, tag, attrs):
        if tag in SafeHTMLParser.acceptable_elements:
            self.has_html = True
        self.add_if_acceptable(tag, attrs)

    def handle_endtag(self, tag):
        self.add_if_acceptable(tag)
        
    def handle_startendtag(self, tag, attrs):
        if tag in SafeHTMLParser.acceptable_elements:
            self.has_html = True
        self.add_if_acceptable(tag, attrs)
    
    def handle_data(self, data):
        self.sanitised += unicode(data, 'utf-8', 'replace')
        
    def handle_charref(self, name):
        self.sanitised += "&#" + name + ";"
    
    def handle_entityref(self, name):
        self.sanitised += "&" + name + ";"

    def feed(self, data):
        HTMLParser.feed(self, data)
        tmp = SafeHTMLParser.multi_replace(data)
        tmp = SafeHTMLParser.uriregex1.sub(
                r'<a href="\1">\1</a>',
                unicode(tmp, 'utf-8', 'replace'))
        tmp = SafeHTMLParser.uriregex2.sub(r'<a href="\1&', tmp)
        tmp = SafeHTMLParser.emailregex.sub(r'<a href="mailto:\1">\1</a>', tmp)
        self.raw += tmp

    def is_html(self, text = None, allow_picture = False):
        if text:
            self.reset()
            self.reset_safe()
            self.allow_picture = allow_picture
            self.feed(text)
            self.close()
        return self.has_html