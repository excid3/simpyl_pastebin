from django.template import Context, loader
from django.http import HttpResponse

def main(request):
    previous = request.POST.get('paste', '')
    
    t = loader.get_template('pastebin/templates/index.html')
    c = Context({
        'previous': previous
    })
    
    return HttpResponse(t.render(c))