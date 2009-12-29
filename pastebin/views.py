from django.template import Context, loader
from django.http import HttpResponse

def main(request):
    t = loader.get_template('pastebin/templates/index.html')
    c = Context(locals())
    return HttpResponse(t.render(c))