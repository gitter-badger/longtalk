
import time
import random
import sys
import os

# Make sure you don't print your access, secret key to the output
# Because sae.const gets the keys from os.environ, if you need the correct
# keys, do this after the importing of sae.const
import sae.util
sae.util.protect_secret(os.environ)

import posix
import math
import bz2

import sae
import sae.core
import sae.const
import sae.util

import pylibmc
mc = pylibmc.Client()

sae.debug = True

# Global test results
r = []

class SandboxError(Exception):
    pass

def get_name(f):
    s = [] 
    if hasattr(f,'__module__'):
        s.append(f.__module__)
    s.append(f.__name__)
    return '.'.join(s)

def trap(e, f, *args):
    fn = get_name(f)
    en = get_name(e)
    c = "%s%s" % (fn, args)
    try:
        f(*args)
    except e:
        r.append('%s: OK, %s raised' % (c, en))
        return True
    raise SandboxError("%s %s not raised" %(c, en))

def sandbox_test():
    global r
    r =[]
    trap(OSError, os.listdir, '/etc')
    trap(OSError, os.listdir, '/tmp')
    trap(IOError, open, '/etc/passwd')
    trap(OSError, os.listdir, '../../')
    trap(OSError, os.listdir, '/data1/www/htdocs/')
    trap(IOError, bz2.BZ2File, '/data1/www/htdocs/test.bz2', 'w')

def list_m(m):
    d = []
    for k in dir(m):
        v = getattr(m, k)
        d.append((k, id(v)))
    return d

def list_d(d):
    r = []
    for k in d.keys():
        v = d[k]
        r.append((k, id(v)))
    return r

def app(environ, start_response):
    sae.util.protect_secret(environ)

    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)

    msg = ['Hello, world!']
    msg.append('cwd: %s' % os.getcwd())
    msg.append('tmp: %s' % sae.core.get_tmp_dir())
    daemon = '-'.join([environ['SERVER_ADDR'], str(os.getpid())])

    msg.append(''.join([ ['o', 'O'][random.randint(0, 1)] for i in range(20)]))
    msg.append(time.ctime())
    msg.append(daemon)

    mc.set("foo", "bar")
    value = mc.get("foo")
    if not mc.get('key'):
        mc.set("key", "1")
    mc.incr("key")

    msg.append('key: %s' % mc.get('key'))
    msg.append('foo: %s' % mc.get('foo'))
    msg.append('')
    output = ['\n'.join(msg)]

    global r
    sandbox_test()
    output.append('\n'.join(r))

    data = {}
    data['sys.path'] = sys.path
    data['sys.version'] = sys.version
    data['os.environ'] = os.environ
    data['environ'] = environ

    i = {}
    i['served_by'] = daemon
    i['sae'] = id(sae)
    i['sae.core.environ'] = id(sae.core.environ)
    #i['sys.modules'] = list_d(sys.modules)
    #i['posix'] = list_m(os)
    #i['os'] = list_m(os)
    i['sae.const'] = [ (k, getattr(sae.const, k)) for k in dir(sae.const) if k != '__builtins__']
    data['isolation_tests'] = i

    import pprint
    output.append(pprint.pformat(data))

    return output

application = sae.create_wsgi_app(app)
