#!/usr/bin/env python

import functools
import markdown
import os.path
import re
import tornado.web
import tornado.wsgi
import unicodedata
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.ext import db

class Msg(db.Model):
    body = db.TextProperty(required=True)

#class Journal:
class Note(db.Model):
    body = db.TextProperty(required = True)
    mtime = db.DateTimeProperty(auto_now = True)
    ctime = db.DateTimeProperty(auto_now_add = True)

# Wrapper for login
def login(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method == "GET":
                self.redirect(self.get_login_url())
                return
            raise tornado.web.HTTPError(403) # Guest POST
        else:
            return method(self, *args, **kwargs)
    return wrapper

class BaseHandler(tornado.web.RequestHandler):
    """Implements Google Accounts authentication methods."""
    def get_current_user(self):
        user = users.get_current_user()
        return user

    def get_login_url(self):
        return users.create_login_url(self.request.uri)

    def render_string(self, template_name, **kwargs):
        # Let the templates access the users module to generate login URLs
        return tornado.web.RequestHandler.render_string(
            self, template_name, users = users, **kwargs)

class HomeHandler(BaseHandler):
    @login
    def get(self):
        notes = db.Query(Note).order('-mtime').fetch(limit = 10)
        self.render("home.html", notes = notes)

class ComposeHandler(BaseHandler):
    @login
    def get(self):
        key = self.get_argument("key", None)
        note = Note.get(key) if key else None
        self.render("compose.html", note = note)

    @login
    def post(self):
        key = self.get_argument("key", None)
        body = self.get_argument("body")
        if key:
            note = Note.get(key)
            note.body = body
        else:
            note = Note(
                body = body,
            )
        note.put()
        self.redirect("/")

settings = {
    "blog_title": u"Personal Notes and Secure Messaging",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
}
application = tornado.wsgi.WSGIApplication([
    (r"/", HomeHandler),
    (r"/compose", ComposeHandler),
], **settings)


def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
