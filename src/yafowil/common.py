import types
from yafowil.base import (
    factory,
    UNSET,
    ExtractionError,
)
from utils import (
    cssclasses,
    cssid,
    tag,
    vocabulary,)

factory.defaults['default'] = None
factory.defaults['class'] = None
factory.defaults['error_class'] = None
factory.defaults['error_class_default'] = 'error'
factory.defaults['required'] = False
factory.defaults['required_message'] = u'Mandatory field was empty'          
factory.defaults['required_class'] = None
factory.defaults['required_class_default'] = 'required'

def _value(widget, data):
    if data.extracted is not UNSET:
        return data.extracted
    if data.value is not UNSET:
        return data.value 
    return widget.attrs.default
    
def generic_extractor(widget, data):
    if widget.dottedpath not in data.request:
        return UNSET
    return data.request[widget.dottedpath]

def generic_required_extractor(widget, data):
    """validate required. 
    
    if required is set and some value was extracted, 
    so data.extracted is not UNSET, then we evaluate data.extracted to boolean.
    raise ExtractionError if result is False
    """
    if not widget.attrs.get('required') \
       or bool(data.extracted) \
       or data.extracted is UNSET:
        return data.extracted
    if isinstance(widget.attrs['required'], basestring):
        raise ExtractionError(widget.attrs['required'])
    raise ExtractionError(widget.attrs['required_message'])

def input_generic_renderer(widget, data):
    input_attrs = {
        'type': data.attrs.get('input_field_type', False) or widget.attrs.type,
        'value':  _value(widget, data),
        'name_': widget.dottedpath,
        'id': cssid(widget, 'input'),    
        'class_': cssclasses(widget, data),    
    }
    return tag('input', **input_attrs)

class InputGenericPreprocessor(object):
    
    def __init__(self, inputtype):
        self.inputtype = inputtype
        
    def __call__(self, widget, data):
        data.attrs['input_field_type'] = self.inputtype   
        return data
    
def register_generic_input(subtype, enable_required_class=True):
    if enable_required_class:
        factory.defaults['%s.required_class' % subtype] = 'required'
    factory.defaults['%s.default' % subtype] = ''
    factory.register(subtype, 
                     [generic_extractor, generic_required_extractor], 
                     [input_generic_renderer],
                     [InputGenericPreprocessor(subtype)])

register_generic_input('text')
register_generic_input('password')
register_generic_input('hidden', False)
register_generic_input('radio')
register_generic_input('checkbox')

def input_file_renderer(widget, data):
    input_attrs = {
        'name_': widget.dottedpath,
        'id': cssid(widget, 'input'),
        'class_': cssclasses(widget, data),            
        'type': 'file',
        'value':  '',
        'accept': widget.attrs.get('accept', None),
    }
    return tag('input', **input_attrs)
    
factory.register('file', 
                 [generic_extractor, generic_required_extractor], 
                 [input_file_renderer])

def select_renderer(widget, data):
    optiontags = [] 
    value = _value(widget, data)
    if isinstance(value, basestring) or not hasattr(value, '__iter__'):
        value = [value]
    for key, term in vocabulary(widget.attrs.get('vocabulary', [])):
        option_attrs = {
            'selected': (key in value) and 'selected' or None,
            'value': key,
            'id': cssid(widget, 'input', key),
        }
        optiontags.append(tag('option', term, **option_attrs))
    select_attrs = {
        'name_': widget.dottedpath,
        'id': cssid(widget, 'input'),
        'class_': cssclasses(widget, data),                        
        'multiple': widget.attrs.multivalued and 'multiple' or None,
    }
    return tag('select', *optiontags, **select_attrs)

factory.defaults['select.multivalued'] = None
factory.defaults['select.default'] = []
factory.register('select', 
                 [generic_extractor], 
                 [select_renderer])

def textarea_renderer(widget, data):
    area_attrs = {
        'name_': widget.dottedpath,
        'id': cssid(widget, 'input'),
        'class_': cssclasses(widget, data),            
        'wrap': widget.attrs.wrap,
        'cols': widget.attrs.cols,
        'rows': widget.attrs.rows,
        'readonly': widget.attrs.readonly and 'readonly',
    }
    value = _value(widget, data)
    return tag('textarea', value, **area_attrs)

factory.defaults['textarea.default'] = ''          
factory.defaults['textarea.wrap'] = None          
factory.defaults['textarea.cols'] = 80          
factory.defaults['textarea.rows'] = 25          
factory.defaults['textarea.readonly'] = None          
factory.register('textarea', 
                 [generic_extractor, generic_required_extractor], 
                 [textarea_renderer])

def submit_renderer(widget, data):
    input_attrs = {
        'name': widget.attrs.action and 'action.%s' % widget.dottedpath,
        'id': cssid(widget, 'input'),
        'class_': widget.attrs.get('class'),
        'type': 'submit',
        'value': widget.attrs.get('label', widget.__name__),
    }
    return tag('input', **input_attrs)

factory.defaults['submit.action'] = None
factory.register('submit', [], [submit_renderer])

def label_renderer(widget, data):
    label_text = widget.attrs.get('label', widget.__name__)
    label_attrs = {
        'for_': cssid(widget, 'input'),
        'class_': cssclasses(widget, data, widget.attrs['class'])
    }
    help = u''
    if widget.attrs.help:
        help_attrs = {'class_': widget.attrs.helpclass}
        help = tag('div', widget.attrs.help, help_attrs)
    pos = widget.attrs.position
    if pos == 'inner':
        return tag('label', label_text, help, data.rendered, **label_attrs)
    elif pos == 'after':
        return data.rendered + tag('label', label_text, help, **label_attrs)
    return tag('label', label_text, help, **label_attrs) + data.rendered

factory.defaults['label.position'] = 'before'
factory.defaults['label.help'] = None
factory.defaults['label.help_class'] = 'help'
factory.register('label', [], [label_renderer])

def field_renderer(widget, data):
    div_attrs = {
        'id': cssid(widget, 'field'),
        'class_': cssclasses(widget, data, widget.attrs['class'])
    }
    return tag('div', data.rendered, **div_attrs)

factory.defaults['field.class'] = 'field'
factory.defaults['field.witherror'] = None
factory.register('field', [], [field_renderer])

def error_renderer(widget, data):
    if not data.errors:
        return data.rendered
    msgs = u''
    for error in data.errors:
        msgs += tag('div', str(error), class_=widget.attrs.message_class)
    return tag('div', msgs, data.rendered, class_=cssclasses(widget, data))

factory.defaults['error.error_class'] = 'error'
factory.defaults['error.message_class'] = 'errormessage'
factory.register('error', [], [error_renderer])