
import functools
import tornado.web

from google.appengine.api import users
from google.appengine.ext import db

from model import *

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

def load_fragments(note, n = None):
    note.fragments_cache = {}
    for key in note.fragments[:n]:
        frag = Fragment.get(key)
        if frag:
            note.fragments_cache[key] = Fragment.get(key)
        else:
            note.fragments.remove(key)
    note.put()

class HomeHandler(BaseHandler):
    @login
    def get(self):
        notes = db.Query(Note).order('-mtime').fetch(limit = 10)
        map(load_fragments, notes)
        self.render("home.html", notes = notes)

class NoteHandler(BaseHandler):
    @login
    def get(self):
        key = self.get_argument("key", None)
        if not key:
            self.redirect("/")
        note = Note.get(key)
        load_fragments(note)
        self.render("note.html", note = note)

class DeleteHandler(BaseHandler):
    @login
    def get(self):
        key = self.get_argument("key", None)
        note = Note.get(key) if key else None
        if note:
            note.delete()
            # FIXME: delete all fragments here
        self.redirect("/")

class SaveHandler(BaseHandler):
    @login
    def post(self):
        #print self.request['POST']
        key = self.get_argument("id", None)
        body = self.get_argument("value", '').strip(' \n')
        frag = Fragment.get(key) if key else None
        if frag:
            if not body:
                frag.delete()
            else:
                frag.body = body
                frag.put()
        self.render("save.html", value = body)

class ComposeHandler(BaseHandler):
    @login
    def get(self):
        key = self.get_argument("key", None)
        note = Note.get(key) if key else None
        self.render("compose.html", note = note)

    @login
    def post(self):
        # Create a new journal or append a fragment to journal
        # TODO: how to edit a journal
        key = self.get_argument("key", None)
        body = self.get_argument("body").strip(' \n')
        title = self.get_argument("title")

        if key:
            note = Note.get(key)
        else:
            note = Note(
                title = title,
                user = self.current_user,)

        frag = Fragment(user = self.current_user, body = body)
        frag.put()
        note.fragments.insert(0, str(frag.key()))
        note.put()

        self.redirect('/note?key=%s' % note.key())
