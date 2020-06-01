# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     hello_world
   Description :
   Author :       zdf's desktop
   date：          2020/5/25
-------------------------------------------------
   Change Activity:
                   2020/5/25:18:23
-------------------------------------------------
"""
import os.path
import random
import textwrap
from abc import ABC
from datetime import datetime

import mistune

import pymongo
from pymongo import MongoClient

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.template

from tornado.options import define, options

define("port", default=80, help="run on the given port", type=int)

'''
try:
    client = pymongo.MongoClient('localhost', 27017)
    db = client['test_db']
    collection = db['articles']
    collection.insert_one({
        "title": "The first test articles",
        "subtitle": "Using tornado to build a personal blog",
        "image": "/static/images/sample.png",
        "author": "ZDF",
        "date_added": 1310248056,
        "date_released": "May 2020",
        "isbn": "978-0-596-52932-1",
        "description": "<p>Lorem ipsum dolor sit amet, audire corrumpit quaerendum eu nec, inermis probatus "
                       "delicatissimi in usu. Eu vis laudem inimicus, vero choro voluptaria eam id. "
                       "Mel diceret mediocritatem et, eum an alia probo. Mel et graecis invidunt scriptorem,"
                       " debet graece noluisse mei ne. Pro ex omnis graece molestiae, ut est eius "
                       "disputationi, cu ius tota persius.</p>",
    })
except Exception as e:
    print(e)
'''


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MainHandler),
            (r'/recent_articles', RecentArticleHandler),
            (r'/add_new_article', NewArticleHandler),
            (r'/daily_pic', DailyPictureHandler),
            (r'/disclaimer', DisclaimerHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={'Article': ArticleModule, 'Picture': PictureModule},
            debug=True,
        )
        try:
            client = pymongo.MongoClient(host='localhost', port=27017)
            self.db = client['test_db']
        except Exception as e:
            print(e)

        tornado.web.Application.__init__(self, handlers, **settings)


class ArticleModule(tornado.web.UIModule):
    def render(self, article):
        return self.render_string('modules/article.html', article=article)

    def css_files(self):
        return os.path.join(os.path.dirname(__file__), '/static/css/sticky-footer-navbar.css')


class PictureModule(tornado.web.UIModule):
    def render(self, picture):
        return self.render_string('modules/single_picture.html', picture=picture)

    def css_files(self):
        return os.path.join(os.path.dirname(__file__), '/static/css/sticky-footer-navbar.css')


class RecentArticleHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        collection = self.application.db['articles']
        articles = collection.find()
        print(articles)
        self.render(
            "recent_articles.html",
            page_title="zdf's website",
            header_text="Recent Articles",
            articles=articles
        )


class DailyPictureHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        collection = self.application.db['pixiv_daily_pics']
        pictures = collection.find()
        url = []
        for picture in pictures:
            temp = picture['filename']
            temp = list(temp)
            temp = "".join(temp)
            temp = 'images\Pixiv\\' + temp
            temp = {'url': temp}
            url.append(temp)
        print(url)
        picture = random.choice(url)
        self.render(
            "daily_picture.html",
            page_title="zdf's website",
            header_text='Daily Picture',
            picture=picture
        )
    
    def post(self):
        query = self.get_argument('upvote')
        query = query[13::]
        query = {"filename": query}
        print(query)
        collection = self.application.db['pixiv_daily_pics']
        picture = {"$inc": {"likes": 1}}
        print(query, " + ", picture)
        collection.find_one_and_update(query, picture)
        self.redirect(
            "/daily_pic",
        )


class NewArticleHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        article = dict()
        self.render(
            "new_article.html",
            page_title="zdf's website",
            header_text="New Article",
            article=article
        )

    def post(self):
        article_fields = ['title', 'subtitle', 'image', 'author', 'description']
        collection = self.application.db['articles']
        article = dict()

        for key in article_fields:
            article[key] = self.get_argument(key, None)
        article['date_added'] = datetime.now().strftime('%a, %b %d %H:%M')
        # Using python markdown parser mistune
        article['description'] = mistune.html(article['description'])
        collection.insert_one(article)
        self.redirect("/recent_articles")


class DisclaimerHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        self.render(
            'disclaimer.html',
            page_title="zdf's website",
            header_text="Disclaimer",
        )


class MainHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        self.render(
            'index.html',
            page_title="zdf's website",
            header_text="welcome to my site!",
        )


if __name__ == "__main__":
    tornado.options.parse_command_line()
    # print(os.path.join(os.path.dirname(__file__), "templates"))
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
