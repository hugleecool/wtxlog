# -*- coding: utf-8 -*-

import time
import random
import markdown
import datetime

from flask import Markup, request

__all__ = ['register_filters', 'markdown_filter']


def markdown_filter(text, codehilite=True):
    """
    代码高亮可选，有的场合不需要高亮，高亮会生成很多代码
    但是fenced_code生成的代码是<pre><code>~~~</code></code>包围的
    """
    exts = [
        'abbr', 'attr_list', 'def_list', 'sane_lists', 'fenced_code', 
        'tables', 'toc', 'wikilinks', 
    ]

    if codehilite:
        exts.append('codehilite(guess_lang=True,linenums=False)')

    return Markup(markdown.markdown(
        text, 
        extensions=exts, 
        safe_mode=False,
    ))



def date_filter(dt, fmt='%Y-%m-%d %H:%M'):
    return dt.strftime(fmt)


def timestamp_filter(stamp, fmt='%Y-%m-%d %H:%M'):
    return datetime.datetime.fromtimestamp(int(stamp)).strftime(fmt)


def register_filters(app):
    app.jinja_env.filters['markdown'] = markdown_filter
    app.jinja_env.filters['date'] = date_filter
    app.jinja_env.filters['timestamp'] = timestamp_filter
