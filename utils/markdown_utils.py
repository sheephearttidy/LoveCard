import re

import bleach
import markdown
from markdown.postprocessors import Postprocessor
from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension


class _StrikethroughPostprocessor(Postprocessor):
    _RE = re.compile(r'~~(.+?)~~')

    def run(self, text):
        return self._RE.sub(r'<del>\1</del>', text)


class _StrikethroughExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(
            _StrikethroughPostprocessor(md), 'strikethrough', 35
        )


class _TaskListTreeprocessor(Treeprocessor):
    def run(self, root):
        for li in root.iter('li'):
            text = li.text or ''
            for child in list(li):
                if child.tag == 'p' and child.text:
                    text = child.text
                    if self._process_task(child, text):
                        break
                break
            else:
                self._process_task_li(li, text)
        return root

    def _process_task(self, p_elem, text):
        m = re.match(r'^\[( |x|X)\]\s+', text)
        if not m:
            return False
        checked = m.group(1).lower() == 'x'
        p_elem.text = None
        cb = p_elem.makeelement('input', {
            'type': 'checkbox',
            'disabled': 'disabled',
        })
        if checked:
            cb.set('checked', 'checked')
        p_elem.insert(0, cb)
        tail = p_elem.makeelement('span', {})
        tail.text = text[m.end():]
        p_elem.insert(1, tail)
        return True

    def _process_task_li(self, li_elem, text):
        m = re.match(r'^\[( |x|X)\]\s+', text)
        if not m:
            return
        checked = m.group(1).lower() == 'x'
        li_elem.text = None
        cb = li_elem.makeelement('input', {
            'type': 'checkbox',
            'disabled': 'disabled',
        })
        if checked:
            cb.set('checked', 'checked')
        cb.tail = text[m.end():]
        li_elem.insert(0, cb)


class _TaskListExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(
            _TaskListTreeprocessor(md), 'task_list', 25
        )


ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'strong', 'em', 'b', 'i', 'u', 'del', 's',
    'blockquote', 'pre', 'code',
    'ul', 'ol', 'li',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'sup', 'sub',
    'div', 'span',
    'input',
    'dl', 'dt', 'dd',
    'abbr',
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'class', 'rel', 'id'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'td': ['align'],
    'th': ['align'],
    'code': ['class'],
    'pre': ['class'],
    'span': ['class'],
    'div': ['class', 'id'],
    'input': ['type', 'disabled', 'checked'],
    'li': ['id', 'class'],
    'sup': ['id'],
    'abbr': ['title'],
    'dl': ['class'],
    'dt': ['id'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


_md = markdown.Markdown(extensions=[
    'fenced_code',
    'footnotes',
    'attr_list',
    'def_list',
    'tables',
    'abbr',
    'sane_lists',
    _StrikethroughExtension(),
    _TaskListExtension(),
])


def render_markdown(text):
    if not text:
        return ''
    _md.reset()
    raw_html = _md.convert(text)
    clean_html = bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return clean_html


_STRIP_MD_RE = re.compile(
    r'!\[.*?\]\(.*?\]'
    r'|\[.*?\]\(.*?\)'
    r'|~~.+?~~'
    r'|[#*_~`>|]'
    r'|^\s*\[[ xX]\]\s'
    r'|^\s*[-*+]\s'
    r'|^\s*\d+\.\s'
    r'|^-{3,}'
    r'|^\+{3,}'
    r'|^\*{3,}'
    r'|^```.*?```'
    , re.MULTILINE | re.DOTALL
)


def strip_markdown(text):
    if not text:
        return ''
    stripped = _STRIP_MD_RE.sub('', text)
    stripped = re.sub(r'\n{2,}', '\n', stripped)
    return stripped.strip()