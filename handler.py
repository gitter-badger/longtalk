
import functools
import tornado.web

from google.appengine.api import users
from google.appengine.ext import db

from model import *

############ Code that I do not know much ##############
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

    def check_permission(self, obj, op = None):
        if obj.user != self.current_user:
            raise tornado.web.HTTPError(403)
        return True

    def load_by_key(self, table, key = 'key'):
        key = self.get_argument(key, None)
        if not key:
            self.redirect("/")
        obj = table.get(key)
        if not obj:
            self.redirect("/")
        # Check permission
        self.check_permission(obj)
        return obj

    def check_xsrf_cookie(self):
        pass

#############################

def load_fragments(note, n = None):
    """Load the first n fragments of a journal"""
    note.fragments_cache = {}
    changed = False
    for key in note.fragments[:n]:
        frag = Fragment.get(key)
        if frag:
            note.fragments_cache[key] = Fragment.get(key)
        else: # Deleted?
            note.fragments.remove(key)
            changed = True
    if changed:
        note.put()

class HomeHandler(BaseHandler):
    @login
    def get(self):
        """"Show 10 latest journals for current user"""
        notes = db.Query(Journal).filter('user = ', self.current_user).order('-mtime').fetch(limit = 10)
        map(load_fragments, notes)
        self.render("home.html", notes = notes)

class NoteHandler(BaseHandler):
    @login
    def get(self):
        """Show a given journal"""
        note = self.load_by_key(Journal)
        load_fragments(note)
        self.render("note.html", note = note)

class DeleteHandler(BaseHandler):
    @login
    def get(self):
        """Delete journal"""
        note = self.load_by_key(Journal)
        note.delete()
        # FIXME: delete all fragments here
        self.redirect("/")

class SaveHandler(BaseHandler):
    @login
    def post(self):
        """Save a fragment"""
        #print self.request['POST']
        body = self.get_argument("value", '').strip(' \n')
        frag = self.load_by_key(Fragment, 'id')
        if not body: # body is empty, user want us to delete the fragment
            frag.delete()
        else:
            frag.body = body
            frag.put()
        self.render("save.html", value = body)

class ComposeHandler(BaseHandler):
    @login
    def get(self):
        """Create a new journal"""
        key = self.get_argument("key", None)
        note = None
        if key:
            note = self.load_by_key(Journal)
        self.render("compose.html", note = note)

    @login
    def post(self):
        """Append a new fragment to journal"""
        key = self.get_argument("key", None)
        body = self.get_argument("body").strip(' \n')
        title = self.get_argument("title")

        if key:# Modify
            note = self.load_by_key(Journal)
        else: # Create
            note = Journal(
                title = title,
                user = self.current_user,)

        frag = Fragment(user = self.current_user, body = body)
        frag.put() # Put first so that we can get its key later
        note.fragments.insert(0, str(frag.key()))
        note.put()

        self.redirect('/note?key=%s' % note.key())
