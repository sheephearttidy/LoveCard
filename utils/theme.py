import os

from flask import render_template, current_app, has_request_context
from jinja2 import BaseLoader, ChoiceLoader, FileSystemLoader, TemplateNotFound

from utils.system import get_config

_THEME_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'themes')


class ThemeLoader(BaseLoader):
    def __init__(self, themes_dir):
        self.themes_dir = os.path.abspath(themes_dir)
        self._fs_loader = FileSystemLoader(self.themes_dir)
        self._theme_dirs = self._scan_theme_dirs()

    def _scan_theme_dirs(self):
        dirs = set()
        if os.path.isdir(self.themes_dir):
            for name in os.listdir(self.themes_dir):
                if os.path.isdir(os.path.join(self.themes_dir, name)):
                    dirs.add(name)
        return dirs

    def get_source(self, environment, template):
        if template.startswith('admin/'):
            raise TemplateNotFound(template)

        first_part = template.split('/')[0]
        if first_part in self._theme_dirs:
            return self._fs_loader.get_source(environment, template)

        theme = _get_current_theme()
        if theme and theme != 'classic' and theme in self._theme_dirs:
            themed_path = theme + '/' + template
            try:
                return self._fs_loader.get_source(environment, themed_path)
            except TemplateNotFound:
                pass

        raise TemplateNotFound(template)


def _get_current_theme():
    if has_request_context():
        try:
            return get_config('siteTheme') or 'classic'
        except Exception:
            return 'classic'
    return 'classic'


def get_theme():
    try:
        return get_config('siteTheme') or 'classic'
    except Exception:
        return 'classic'


def render_themed(template, **kwargs):
    return render_template(template, **kwargs)


def setup_theme_loader(app):
    theme_dir = os.path.join(app.root_path, 'themes')
    theme_dir = os.path.abspath(theme_dir)
    if not os.path.isdir(theme_dir):
        return

    theme_loader = ThemeLoader(theme_dir)
    original = app.jinja_loader

    if isinstance(original, ChoiceLoader):
        app.jinja_loader = ChoiceLoader([theme_loader] + original.loaders)
    else:
        app.jinja_loader = ChoiceLoader([theme_loader, original])


def clear_template_cache():
    try:
        current_app.jinja_env.cache.clear()
    except Exception:
        pass


def list_themes():
    result = {}
    if not os.path.isdir(_THEME_DIR):
        return {'classic': '经典'}
    for name in os.listdir(_THEME_DIR):
        theme_path = os.path.join(_THEME_DIR, name)
        if os.path.isdir(theme_path) and os.path.isfile(os.path.join(theme_path, 'base.html')):
            meta = _read_theme_meta(theme_path)
            result[name] = meta.get('name', name)
    if 'classic' not in result:
        result['classic'] = '经典'
    return result


def _read_theme_meta(theme_path):
    meta = {}
    meta_file = os.path.join(theme_path, 'theme.json')
    if os.path.isfile(meta_file):
        try:
            import json
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception:
            pass
    return meta