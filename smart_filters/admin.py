from django.contrib import admin
from django.conf import settings
from django.http import HttpResponseRedirect, QueryDict

PREFIX = getattr(settings, 'SMART_FILTERS_PREFIX', 'SMARTFILTER_')
COOKIE_AGE = getattr(settings, 'SMART_FILTERS_COOKIE_AGE', 60*60*4)

class SmartFilterMixin(object):
    change_list_template = 'admin/change_list_smart.html'
    
    def get_default_querystring(self, request):
        """Send users to this querystring if they haven't been here yet 
        (or their cookie expired)."""
        return
    
    def get_title(self, request, filters):
        """Hook to vary the title based on filters and request. 
        Return None for django admin default."""
        return self.model._meta.verbose_name_plural.title()
        
    def get_filter_msg(self, request, filters):
        """Hook to vary the filter message based on filters and request
        Return None to hide the filter message."""
        return ', '.join([ '%s: %s' % (k.title(), v) for k, v in filters.items() ])

    def changelist_view(self, request, extra_context=None):
        key = PREFIX + str(hash(request.path))
        if request.GET.has_key('clear'):
            response = HttpResponseRedirect('?')
            response.set_cookie(key, 'ALL')
            return response
        current = request.META['QUERY_STRING']
        if current == '':
            redir = request.COOKIES.get(key, self.get_default_querystring(request))
            if redir and redir != 'ALL':
                return HttpResponseRedirect('?%s' % redir)
        extra_context = extra_context or {}
        save = QueryDict('', mutable=True)
        filters = {}
        for param, value in request.GET.items():
            if '__' in param:
                param = str(param)
                parts = param.split('__')
                try:
                    field = self.model._meta.get_field_by_name(parts[0])[0]
                    fieldname = field.verbose_name
                except:
                    continue
                label = '(filtered)'
                if '__exact' in param:
                    save[param] = value
                    try:
                        label = dict([ (str(k), str(v)) for k, v in field.get_choices() ])[str(value)]
                    except:
                        label = field.to_python(value)
                filters[fieldname] = label 
        if filters:
            filter_msg = self.get_filter_msg(request, filters)
            if filter_msg:
                extra_context['filter_msg'] = filter_msg
        title = self.get_title(request, filters)
        if title:
            extra_context['title'] = title
        response = super(SmartFilterMixin, self).changelist_view(request, extra_context)
        if save:
            response.set_cookie(key, value=save.urlencode(), max_age=COOKIE_AGE)
        return response
