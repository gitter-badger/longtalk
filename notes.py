#!/usr/bin/env python

import functools
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
    title = db.TextProperty()
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

class NoteHandler(BaseHandler):
    @login
    def get(self):
        key = self.get_argument("key", None)
        if not key:
            self.redirect("/")

        note = Note.get(key)
        self.render("note.html", note = note)


class DeleteHandler(BaseHandler):
    @login
    def get(self):
        key = self.get_argument("key", None)
        note = Note.get(key) if key else None
        if note:
            note.delete()
        self.redirect("/")

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
        title = self.get_argument("title")
        append = self.get_argument("append", None)
        if key:
            note = Note.get(key)
            if append:
                # Append mode
                note.body = body + '\n\n' + note.body
            else:
                # Edit mode
                note.body = body
                note.title = title
        else:
            # Create mode
            note = Note(
                title = title,
                body = body,
            )
        note.put()
        self.redirect('/note?key=%s' % note.key())

settings = {
    "blog_title": u"Personal Notes and Secure Messaging",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
}
application = tornado.wsgi.WSGIApplication([
    (r"/", HomeHandler),
    (r"/compose", ComposeHandler),
    (r"/delete", DeleteHandler),
    (r"/note", NoteHandler),
], **settings)


def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
