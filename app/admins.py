# -*- coding: utf-8 -*-

from urllib import unquote
from datetime import datetime
from flask import redirect, url_for, Markup, flash
from flask.ext.login import current_user, login_required
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose, helpers
from flask.ext.admin.contrib import sqla
from flask.ext.admin.actions import action
from webhelpers.html import HTML
from webhelpers.html.tags import link_to

from wtforms.fields import SelectField, TextAreaField
from .utils.helpers import baidu_ping
from .utils.widgets import MarkitupTextAreaField, CKTextAreaField
from .ext import cache
from .models import *

from config import Config

BODY_FORMAT = Config.BODY_FORMAT
if BODY_FORMAT == 'html':
    EDITOR_WIDGET = CKTextAreaField
else:
    EDITOR_WIDGET = MarkitupTextAreaField

cache_key = Config.MEMCACHE_KEY


def cache_delete(key):
    cache.cache.delete(cache_key % key)
    cache.cache.delete(cache_key % ('mobile%s' % key))


def format_datetime(self, request, obj, fieldname, *args, **kwargs):
    return getattr(obj, fieldname).strftime("%Y-%m-%d %H:%M")


def view_on_site(self, request, obj, fieldname, *args, **kwargs):
    return Markup('%s%s' % (
        HTML.i(style='margin-right:5px;', class_='icon icon-eye-open'),
        link_to(u'预览', obj.link, target='_blank'),
    ))


class MyAdminIndexView(AdminIndexView):

    @expose('/')
    @login_required
    def index(self):
        if not current_user.is_authenticated():
            return redirect(url_for('account.login'))
        return super(MyAdminIndexView, self).index()


# Customized Post model admin
class ArticleAdmin(sqla.ModelView):
    # Visible columns in the list view
    
    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"

    column_list = ('title', 'category', 'tags', 'published', 'ontop', 
            'recommend', 'created', 'view_on_site')

    form_excluded_columns = ('author', 'summary', 'body_html', 
                             'hits', 'created', 'last_modified',)

    # List of columns that can be sorted. For 'user' column, use User.username as
    # a column.
    # column_sortable_list = ('created', 'title',)

    column_labels = dict(
            title=u'文章标题',
            category=u'栏目',
            published=u'已发布',
            tags=u'标签',
            ontop=u'置顶',
            recommend=u'推荐',
            created=u'创建时间',
            view_on_site=u'预览'
    )
    
    column_searchable_list = ('title',)

    column_formatters = dict(
            view_on_site=view_on_site,
            created=format_datetime,
    )

    form_create_rules = (
            'title', 'seotitle', 'category', 'topic', 'tags', 'body',
            'published', 'ontop', 'recommend', 'seokey', 'seodesc',
            'thumbnail', 'thumbnail_big', 'template'
    )
    form_edit_rules = form_create_rules

    form_overrides = dict(seodesc=TextAreaField, body=EDITOR_WIDGET)
    
    form_widget_args = {
        'title': {'style': 'width:480px;'}, 
        'slug': {'style': 'width:480px;'}, 
        'seotitle': {'style': 'width:480px;'}, 
        'seokey': {'style': 'width:480px;'}, 
        'seodesc': {'style': 'width:480px; height:80px;'}, 
        'thumbnail': {'style': 'width:480px;'}, 
        'thumbnail_big': {'style': 'width:480px;'}, 
        'template': {'style': 'width:480px;'}, 
        'summary': {'style': 'width:635px; height:80px;font-family:monospace;'},
    }

    # Pass arguments to WTForms. In this case, change label for text field to
    # be 'Big Text' and add required() validator.
    form_args = dict(
        slug=dict(description=u'英文唯一标识符，建议小写英文字母、数字'),
        title=dict(description=u'文章标题，极为重要'),
        seotitle=dict(description=u'SEO标题'),
        seokey=dict(description=u'SEO关键词'),
        seodesc=dict(description=u'SEO描述'),
        thumbnail=dict(description=u'图片规格建议100*100像素'),
        thumbnail_big=dict(description=u'大缩略图，根据实际情况确定尺寸'),
        template=dict(description=u'模板文件，使用默认请留空'),
        summary=dict(description=u'文章摘要，建议认真填写(不超过3行半)'),
        body=dict(description=u'文章内容，格式为Markdown格式'),
        body_html=dict(description=u'此项为程序根据body自动生成'),
        published=dict(description=u'是否发布，打勾表示发布'),
        ontop=dict(description=u'是否置顶，打勾表示置顶'),
        recommend=dict(description=u'是否推荐，打勾表示推荐'),
    )

    # Model handlers
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.author_id = current_user.id
            model.created = datetime.now()
            model.last_modified = model.created
        else:
            model.last_modified = datetime.now()

    def after_model_change(self, form, model, is_created):
        # 如果发布新文章，则PING通知百度
        if is_created and model.published:
            baidu_ping(model.link)

        # 清除缓存，以便可以看到最新内容
        cache_delete(model.shortlink)

    def is_accessible(self):
        return current_user.is_administrator()

    @action('pingbaidu', 'Ping to Baidu')
    def action_ping_baidu(self, ids):
        for id in ids:
            obj = Article.query.get(id)
            baidu_ping(obj.link)
        flash(u'PING请求已发送，请等待百度处理')
        

class CategoryAdmin(sqla.ModelView):

    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"
    
    #column_exclude_list = ['thumbnail']
    column_list = ('name', 'longslug', 'seotitle', 'view_on_site')

    column_searchable_list = ('slug', 'longslug', 'name')

    form_excluded_columns = ('articles', 'body_html', 'longslug', 'children')

    form_overrides = dict(seodesc=TextAreaField, body=EDITOR_WIDGET)

    column_formatters = dict(view_on_site=view_on_site)

    form_widget_args = { 
        'slug': {'style': 'width:320px;'}, 
        'name': {'style': 'width:320px;'}, 
        'thumbnail': {'style': 'width:480px;'}, 
        'seotitle': {'style': 'width:480px;'}, 
        'seokey': {'style': 'width:480px;'}, 
        'seodesc': {'style': 'width:480px; height:80px;'}, 
        'template': {'style': 'width:480px;'}, 
        'article_template': {'style': 'width:480px;'}, 
    }

    form_args = dict(
        slug=dict(description=u'英文唯一标识符，建议小写英文字母、数字'),
        name=dict(description=u'栏目名称'),
        thumbnail=dict(description=u'缩略图URL'),
        seotitle=dict(description=u'SEO标题，空白的话默认与栏目名称相同'),
        seokey=dict(description=u'栏目SEO关键词'),
        seodesc=dict(description=u'栏目SEO描述'),
        template=dict(description=u'栏目列表页模板，使用默认请留空'),
        article_template=dict(description=u'栏目文章页模板，使用默认请留空'),
        body=dict(description=u'栏目详细介绍'),
    )

    # Model handlers
    def on_model_change(self, form, model, is_created):
        if not model.id:
            c = Category.query.filter_by(name=model.name).first()
            if c:
                raise Exception('Category "%s" already exist' % c.name)

            if not model.seotitle:
                model.seotitle = model.name

            if not model.seokey:
                model.seokey = model.name

    def after_model_change(self, form, model, is_created):
        cache_delete(model.shortlink)

    def is_accessible(self):
        return current_user.is_administrator()


class TagAdmin(sqla.ModelView):

    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"
    
    #column_exclude_list = ['thumbnail']
    column_list = ('name', 'seotitle', 'seokey', 'view_on_site')

    column_searchable_list = ('name',)

    form_excluded_columns = ('articles', 'body_html')

    form_overrides = dict(seodesc=TextAreaField, body=EDITOR_WIDGET)

    column_formatters = dict(view_on_site=view_on_site)

    form_widget_args = {
        'slug': {'style': 'width:320px;'}, 
        'name': {'style': 'width:320px;'}, 
        'thumbnail': {'style': 'width:480px;'}, 
        'seotitle': {'style': 'width:480px;'}, 
        'seokey': {'style': 'width:480px;'}, 
        'seodesc': {'style': 'width:480px; height:80px;'}, 
        'template': {'style': 'width:480px;'}, 
    }

    form_args = dict(
        slug=dict(description=u'英文唯一标识符，建议小写英文字母、数字'),
        name=dict(description=u'Tag名称'),
        thumbnail=dict(description=u'缩略图'),
        seotitle=dict(description=u'SEO标题，空白的话默认与Tag名称相同'),
        seokey=dict(description=u'Tag关键词'),
        seodesc=dict(description=u'Tag描述'),
        template=dict(description=u'列表页模板，使用默认请留空'),
        body=dict(description=u'Tag详细介绍'),
    )

    # Model handlers
    def on_model_change(self, form, model, is_created):
        if not model.id:
            t = Tag.query.filter_by(name=model.name).first()
            if t:
                raise Exception('Tag "%s" already exist' % t.name)

            if not model.seotitle:
                model.seotitle = model.name

            if not model.seokey:
                model.seokey = model.name

    def after_model_change(self, form, model, is_created):
        # 中文的路径特别需要注意
        #cache_delete(unquote(model.shortlink))
        cache_delete(model.shortlink)
            
    def is_accessible(self):
        return current_user.is_administrator()


class TopicAdmin(sqla.ModelView):

    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"
    
    #column_exclude_list = ['thumbnail']
    column_list = ('name', 'slug', 'seotitle', 'view_on_site')

    form_excluded_columns = ('articles', 'body_html')

    column_searchable_list = ('slug', 'name')

    form_overrides = dict(seodesc=TextAreaField, body=EDITOR_WIDGET)

    column_formatters = dict(view_on_site=view_on_site)

    form_widget_args = { 
        'slug': {'style': 'width:320px;'}, 
        'name': {'style': 'width:320px;'}, 
        'thumbnail': {'style': 'width:480px;'}, 
        'seotitle': {'style': 'width:480px;'}, 
        'seokey': {'style': 'width:480px;'}, 
        'seodesc': {'style': 'width:480px; height:80px;'}, 
        'template': {'style': 'width:480px;'}, 
    }

    form_args = dict(
        slug=dict(description=u'英文唯一标识符，建议小写英文字母、数字'),
        name=dict(description=u'栏目名称'),
        thumbnail=dict(description=u'缩略图URL'),
        seotitle=dict(description=u'SEO标题，空白的话默认与栏目名称相同'),
        seokey=dict(description=u'栏目SEO关键词'),
        seodesc=dict(description=u'栏目SEO描述'),
        template=dict(description=u'栏目列表页模板，使用默认请留空'),
        body=dict(description=u'栏目详细介绍'),
    )

    # Model handlers
    def on_model_change(self, form, model, is_created):
        if not model.id:
            t = Topic.query.filter_by(name=model.name).first()
            if t:
                raise Exception('Topic "%s" already exist' % t.name)

            if not model.seotitle:
                model.seotitle = model.name

            if not model.seokey:
                model.seokey = model.name

    def after_model_change(self, form, model, is_created):
        cache_delete(model.shortlink)

    def is_accessible(self):
        return current_user.is_administrator()

class FlatpageAdmin(sqla.ModelView):

    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"

    #column_exclude_list = ['body', 'body_html', 'summary',]
    column_list = ('title', 'slug', 'seotitle', 'view_on_site')

    column_searchable_list = ('slug', 'title', )

    column_formatters = dict(view_on_site=view_on_site)

    form_excluded_columns = ('body_html', )

    form_overrides = dict(seodesc=TextAreaField, body=EDITOR_WIDGET)

    form_widget_args = {
        'title': {'style': 'width:480px;'}, 
        'slug': {'style': 'width:320px;'}, 
        'seotitle': {'style': 'width:480px;'}, 
        'seokey': {'style': 'width:480px;'}, 
        'seodesc': {'style': 'width:480px; height:80px;'}, 
        'template': {'style': 'width:480px;'}, 
    }

    form_args = dict(
        slug=dict(description=u'英文唯一标识符，建议小写英文字母、数字'),
        title=dict(description=u'页面标题'),
        seotitle=dict(description=u'SEO标题'),
        seokey=dict(description=u'SEO关键词'),
        seodesc=dict(description=u'SEO描述'),
        template=dict(description=u'内容页模板，使用默认请留空'),
        body=dict(description=u'内容'),
    )

    def is_accessible(self):
        return current_user.is_administrator()

    def on_model_change(self, form, model, is_created):
        pass

    def after_model_change(self, form, model, is_created):
        cache_delete(model.shortlink)


class FriendLinkAdmin(sqla.ModelView):
    
    column_exclude_list = ['note']

    column_searchable_list = ('anchor', 'title', 'url')

    form_overrides = dict(note=TextAreaField)

    form_widget_args = {
        'anchor': {'style': 'width:320px;'}, 
        'title': {'style': 'width:320px;'}, 
        'url': {'style': 'width:480px;'}, 
        'note': {'style': 'width:480px; height:80px;'}, 
    }

    form_args = dict(
        anchor=dict(description=u'锚文本'),
        title=dict(description=u'显示标题'),
        url=dict(description=u'链接URL'),
    )

    def is_accessible(self):
        return current_user.is_administrator()


class LinkAdmin(sqla.ModelView):

    column_exclude_list = ['note']
    
    form_overrides = dict(note=TextAreaField)

    form_widget_args = {
        'title': {'style': 'width:320px;'}, 
        'url': {'style': 'width:480px;'}, 
        'note': {'style': 'width:480px; height:80px;'}, 
    }

    form_args = dict(
        anchor=dict(description=u'锚文本'),
        title=dict(description=u'显示标题'),
        url=dict(description=u'链接URL'),
    )

    def is_accessible(self):
        return current_user.is_administrator()


class LabelAdmin(sqla.ModelView):

    column_list = ('slug', 'title')

    column_searchable_list = ('slug', 'title')
    
    form_overrides = dict(html=TextAreaField)

    form_widget_args = {
        'slug': {'style': 'width:480px;'}, 
        'title': {'style': 'width:480px;'}, 
        'html': {'style': 'width:640px; height:320px;'}, 
    }

    form_args = dict(
        slug=dict(description=u'英文唯一标识符，建议小写英文字母、数字'),
        title=dict(description=u'标签标题'),
        html=dict(description=u'HTML代码'),
    )

    def is_accessible(self):
        return current_user.is_administrator()


class RedirectAdmin(sqla.ModelView):

    column_searchable_list = ('old_path', 'new_path')

    form_overrides = dict(note=TextAreaField)

    form_widget_args = {
        'old_path': {'style': 'width:320px;'}, 
        'new_path': {'style': 'width:320px;'}, 
        'note': {'style': 'width:480px; height:80px;'}, 
    }

    form_args = dict(
        old_path=dict(description=u'旧路径'),
        new_path=dict(description=u'要转向的新路径'),
        note=dict(description=u'备注'),
    )
    
    def is_accessible(self):
        return current_user.is_administrator()


class UserAdmin(sqla.ModelView):

    column_list = ('email', 'username', 'name', 'role', 'confirmed')

    form_excluded_columns = ('password_hash', 'avatar_hash', 'articles', 'member_since', 'last_seen')

    column_searchable_list = ('email', 'username', 'name')

    form_overrides = dict(about_me=TextAreaField)

    form_widget_args = {
        'about_me': {'style': 'width:480px; height:80px;'}, 
    }

    def is_accessible(self):
        return current_user.is_administrator()


# init
admin = Admin(index_view=MyAdminIndexView(), base_template="admin/my_master.html")

# add views
admin.add_view(TopicAdmin(Topic, db.session, name=u'专题'))
admin.add_view(CategoryAdmin(Category, db.session, name=u'栏目'))
admin.add_view(TagAdmin(Tag, db.session, name=u'标签'))
admin.add_view(ArticleAdmin(Article, db.session, name=u'文章'))
admin.add_view(FlatpageAdmin(Flatpage, db.session, name=u'单页面'))

admin.add_view(LabelAdmin(Label, db.session, u'静态标签'))

#admin.add_view(LinkAdmin(Link, db.session, category=u'链接', name=u'内部链接'))
admin.add_view(FriendLinkAdmin(FriendLink, db.session, name=u'友情链接'))
admin.add_view(RedirectAdmin(Redirect, db.session, name=u'重定向'))

admin.add_view(UserAdmin(User, db.session, name=u'用户'))

