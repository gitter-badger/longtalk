
from google.appengine.ext import db

class Fragment(db.Model):
    user =  db.UserProperty(required=True)
    mtime = db.DateTimeProperty(auto_now = True)
    ctime = db.DateTimeProperty(auto_now_add = True)
    body = db.StringProperty()

#class Journal:
class Journal(db.Model):
    user =  db.UserProperty(required=True)
    mtime = db.DateTimeProperty(auto_now = True)
    ctime = db.DateTimeProperty(auto_now_add = True)
    title = db.StringProperty()
    # Save the reference to fragments
    fragments = db.StringListProperty()

Note = Journal

