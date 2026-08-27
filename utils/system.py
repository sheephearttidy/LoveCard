from model.System import System
from model.db import db


SITE_CONFIG_DEFAULTS = {
    'siteName': 'LoveCards',
    'siteSubTitle': '表白墙',
    'siteDesc': '用心传递每一份情感，让爱不再沉默',
    'siteUrl': '',
    'siteIcp': '',
    'siteFooter': '用心传递每一份情感',
    'siteKeyword': '',
    'siteAllowRegister': 'true',
    'siteAllowPublish': 'true',
    'siteCardNeedReview': 'true',
}

SITE_CONFIG_LABELS = {
    'siteName': '站点名称',
    'siteSubTitle': '站点副标题',
    'siteDesc': '站点描述',
    'siteUrl': '站点URL',
    'siteIcp': 'ICP备案号',
    'siteFooter': '页脚信息',
    'siteKeyword': '站点关键词',
    'siteAllowRegister': '允许注册',
    'siteAllowPublish': '允许发布',
    'siteCardNeedReview': '卡片需审核',
}

SITE_CONFIG_GROUPS = [
    {
        'title': '基本设置',
        'icon': 'fa-globe',
        'fields': ['siteName', 'siteSubTitle', 'siteDesc', 'siteUrl', 'siteKeyword'],
    },
    {
        'title': '页脚与备案',
        'icon': 'fa-file-contract',
        'fields': ['siteFooter', 'siteIcp'],
    },
    {
        'title': '功能开关',
        'icon': 'fa-toggle-on',
        'fields': ['siteAllowRegister', 'siteAllowPublish', 'siteCardNeedReview'],
    },
]

SITE_CONFIG_HINTS = {
    'siteName': '显示在导航栏、页面标题等位置',
    'siteSubTitle': '显示在首页标题后方，如"表白墙"',
    'siteDesc': '站点简介，显示在首页副标题和meta描述中',
    'siteUrl': '站点完整URL，如 https://example.com',
    'siteIcp': 'ICP备案号，显示在页脚，留空则不显示',
    'siteFooter': '页脚版权文字，显示在页面底部',
    'siteKeyword': 'SEO关键词，多个用逗号分隔',
    'siteAllowRegister': 'true=允许新用户注册，false=关闭注册',
    'siteAllowPublish': 'true=允许发布卡片，false=关闭发布',
    'siteCardNeedReview': 'true=新卡片需审核后才显示，false=直接显示',
}


def get_site_config():
    configs = db.session.execute(db.select(System)).scalars().all()
    config_dict = {c.name: c.value for c in configs}
    result = dict(SITE_CONFIG_DEFAULTS)
    result.update(config_dict)
    return result


def get_config(name):
    item = db.session.execute(
        db.select(System).where(System.name == name)
    ).scalar()
    if item:
        return item.value
    return SITE_CONFIG_DEFAULTS.get(name, '')


def set_config(name, value):
    item = db.session.execute(
        db.select(System).where(System.name == name)
    ).scalar()
    if item:
        item.value = value
    else:
        db.session.add(System(name=name, value=value))


def ensure_default_configs():
    for name, value in SITE_CONFIG_DEFAULTS.items():
        existing = db.session.execute(
            db.select(System).where(System.name == name)
        ).scalar()
        if not existing:
            db.session.add(System(name=name, value=value))
    db.session.commit()