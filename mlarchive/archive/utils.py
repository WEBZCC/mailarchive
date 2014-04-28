try:
    import json
except ImportError:
    import simplejson as json

import mailbox

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

from mlarchive.archive.models import EmailList


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def get_noauth(request):
    """This function takes a request object and returns a list of private email list names
    (as string) the user does NOT have access to, for use in an exclude().  The list is
    stored in the request session to minimize database hits.
    """
    noauth = request.session.get('noauth',None)
    if noauth:
        return noauth
    else:
        request.session['noauth'] = [ str(x.id) for x in EmailList.objects.filter(
            private=True).exclude(members=request.user) ]
        return request.session['noauth']

def jsonapi(fn):
    def to_json(request, *args, **kwargs):
        context_data = fn(request, *args, **kwargs)
        return HttpResponse(json.dumps(context_data),
                mimetype='application/json')
    return to_json

'''
def render(template, data, request):
    return render_to_response(template,
                              data,
                              context_instance=RequestContext(request))

def template(template):
    def decorator(fn):
        def render(request, *args, **kwargs):
            context_data = fn(request, *args, **kwargs)
            if isinstance(context_data, HttpResponse):
                # View returned an HttpResponse like a redirect
                return context_data
            else:
                # For any other type of data try to populate a template
                return render_to_response(template,
                        context_data,
                        context_instance=RequestContext(request)
                    )
        return render
    return decorator
'''
