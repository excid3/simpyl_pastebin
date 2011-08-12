# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cgi

from django import http
from django.template import Context, loader
from django.shortcuts import get_object_or_404

import settings

from models import Paste

import unicodedata
import datetime

titl = getattr(settings, 'SIMPYL_PASTEBIN_TITLE', 'Simpyl Pastebin')

def set_cookie(response, key, value, days_expire = 7):
    if not hasattr(settings, 'SESSION_COOKIE_DOMAIN') or not hasattr(settings, 'SESSION_COOKIE_SECURE'):
        return None
    
    if days_expire is None:
        max_age = 365*24*3600
    else:
        max_age = days_expire*24*3600
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires, domain=settings.SESSION_COOKIE_DOMAIN, secure=settings.SESSION_COOKIE_SECURE or None)
    return response

def sanitize_nasty(txt) :
    if not isinstance(txt, str) :
        txt = unicodedata.normalize('NFKD', txt).encode('ascii','ignore')
    return (''.join([c for c in txt if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- .,^']))

def sanitize_username(user_name) :
    return sanitize_nasty(user_name)[0:50]

def main(request):
    previous = request.POST.get('paste', '')

    user_name = ''

    user_name_post = request.POST.get('user_name', '')

    if 'user_name' in request.COOKIES :
        user_name = sanitize_username(request.COOKIES['user_name'])
    
    if user_name_post :
        user_name = sanitize_username(user_name_post)

    ucookie = False

    if previous:
        try:
            import hashlib
            id = hashlib.md5(previous).hexdigest()
        except:
            import md5
            id = md5.new(previous).hexdigest()

        id = id[0:12]

        try:
            Paste.objects.get(url=id)
        except:
            p = Paste(content=previous, url=id)
            p.save()
        
        previous = 'http://%s/%s' % (sanitize_nasty(request.get_host()), id)

        if hasattr(settings, 'SIMPYL_PASTEBIN_ZMQ_URL') :
            import zmq
            ztx = zmq.Context()
            pub = ztx.socket(zmq.PUB)
            pub.connect(settings.SIMPYL_PASTEBIN_ZMQ_URL)

            if not user_name :
                try :
                    user_name = sanitize_username(request.META['HTTP_X_REAL_IP'])
                except :
                    user_name = request.META['REMOTE_ADDR']
            else :
                ucookie = user_name

            pub.send("action::paste by %s: %s" % (user_name, previous))
            
    t = loader.get_template('index.html')

    cdict = {
        'title': titl,
        'title_low': titl.lower(),
        'previous': previous,
        'user_name': user_name
    }

    if hasattr(settings, 'SIMPYL_PASTEBIN_NOTELINE') :
        cdict['noteline'] = settings.SIMPYL_PASTEBIN_NOTELINE

    if hasattr(settings, 'GA_ID') :
        cdict['GA_ID'] = settings.GA_ID

    c = Context(cdict)
    
    resp = http.HttpResponse(t.render(c))
    if ucookie :
        set_cookie(resp, 'user_name', ucookie, days_expire=365)
    return resp

def fetch_paste(request):
    url = request.META.get('PATH_INFO', '')[1:]
    content = ""
    
    try:
        p = Paste.objects.get(url=url)
    except:
        t = loader.get_template('index.html')
        c = Context({
        'title': titl + ' 404',
        'title_low': titl.lower() + ' 404',
            'error': "Paste requested does not exist."
        })
        return http.HttpResponse(t.render(c))
    
    repl = [
        ("\t", "  "),
        (" ", "&nbsp;"),
        ("\n","<br />")
    ]

    esc_text = cgi.escape(p.content)
    for a,b in repl :
        esc_text = esc_text.replace(a,b)

    if hasattr(settings, 'SIMPYL_PASTEBIN_NOTELINE') :
        noteline = cgi.escape(settings.SIMPYL_PASTEBIN_NOTELINE)
    else :
        noteline = ''

    return http.HttpResponse("<h1>paste.</h1><br /><a href=\"/\">make another</a><br />%s<br /><br /><tt>%s</tt>" % (noteline, esc_text))
