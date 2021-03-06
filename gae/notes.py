#!/usr/bin/env python

import os.path
import tornado.wsgi
import wsgiref.handlers

from handler import *

settings = {
    "blog_title": "LongTalk",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
}
application = tornado.wsgi.WSGIApplication([
    (r"/", HomeHandler),
    (r"/compose", ComposeHandler),
    (r"/delete", DeleteHandler),
    (r"/note", NoteHandler),
    (r"/save", SaveHandler),
], **settings)

def main():
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
