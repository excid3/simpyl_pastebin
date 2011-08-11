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

def main(request):
    previous = request.POST.get('paste', '')
    
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
        
        previous = 'http://%s/%s' % (request.get_host(), id)

        if hasattr(settings, 'SIMPYL_PASTEBIN_ZMQ_URL') :
            import zmq
            ztx = zmq.Context()
            pub = ztx.socket(zmq.PUB)
            pub.connect(settings.SIMPYL_PASTEBIN_ZMQ_URL)

            try :
                remote_ip = request.META['HTTP_X_REAL_IP']
            except :
               remote_ip = request.META['REMOTE_ADDR']

            pub.send("action::paste by %s: %s" % (remote_ip, previous))
            
    t = loader.get_template('index.html')
    c = Context({
        'previous': previous
    })
    
    return http.HttpResponse(t.render(c))


def fetch_paste(request):
    url = request.META.get('PATH_INFO', '')[1:]
    content = ""
    
    try:
        p = Paste.objects.get(url=url)
    except:
        t = loader.get_template('index.html')
        c = Context({
            'error': "Paste '%s' does not exist." % url
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

    return http.HttpResponse("<h1>paste.</h1><br /><a href=\"/\">make another</a><br /><br /><tt>" + esc_text + "</tt>")

