import time
import datetime

from flask.ext import wtf
from wtforms import fields, widgets

from flask_superadmin.babel import gettext
from flask import request

class BaseForm(wtf.Form):
    """
        Customized form class.
    """
    def __init__(self, formdata=None, obj=None, prefix='', **kwargs):
        if formdata:
            super(BaseForm, self).__init__(formdata, obj, prefix, **kwargs)
        else:
            super(BaseForm, self).__init__(obj=obj, prefix=prefix, **kwargs)

        self._obj = obj

    @property
    def has_file_field(self):
        """
            Return True if form contains at least one FileField.
        """
        # TODO: Optimize me
        for f in self:
            if isinstance(f, fields.FileField):
                return True

        return False


class TimeField(fields.Field):
    """
        A text field which stores a `datetime.time` object.
        Accepts time string in multiple formats: 20:10, 20:10:00, 10:00 am, 9:30pm, etc.
    """
    widget = widgets.TextInput()

    def __init__(self, label=None, validators=None, formats=None, **kwargs):
        """
            Constructor

            `label`
                Label
            `validators`
                Field validators
            `formats`
                Supported time formats, as a enumerable.
            `kwargs`
                Any additional parameters
        """
        super(TimeField, self).__init__(label, validators, **kwargs)

        self.formats = formats or ('%H:%M:%S', '%H:%M',
                                  '%I:%M:%S%p', '%I:%M%p',
                                  '%I:%M:%S %p', '%I:%M %p')

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.formats[0]) or u''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = u' '.join(valuelist)

            for format in self.formats:
                try:
                    timetuple = time.strptime(date_str, format)
                    self.data = datetime.time(timetuple.tm_hour,
                                              timetuple.tm_min,
                                              timetuple.tm_sec)
                    return
                except ValueError:
                    pass

            raise ValueError(gettext('Invalid time format'))


class ChosenSelectWidget(widgets.Select):
    """
        `Chosen <http://harvesthq.github.com/chosen/>`_ styled select widget.

        You must include chosen.js and form.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        if getattr(field, 'allow_blank', False) and not self.multiple:
            kwargs['data-role'] = u'chosenblank'
        else:
            kwargs['data-role'] = u'chosen'

        return super(ChosenSelectWidget, self).__call__(field, **kwargs)


class ChosenSelectField(fields.SelectField):
    """
        `Chosen <http://harvesthq.github.com/chosen/>`_ styled select field.

        You must include chosen.js and form.js for styling to work.
    """
    widget = ChosenSelectWidget

class FileFieldWidget(object):
    # widget_file = widgets.FileInput()
    widget_checkbox = widgets.CheckboxInput()
    def __call__(self, field, **kwargs):
        from cgi import escape
        input_file = '<input %s>' % widgets.html_params(name=field.name, type='file')
        return widgets.HTMLString('%s<br />Current: %s<br />%s <label for="%s">Clear file</label>'%(input_file, escape(field._value()), self.widget_checkbox(field._clear), field._clear.id))

class FileField(fields.FileField):
    widget = FileFieldWidget()
    def __init__(self,*args,**kwargs):
        self.clearable = kwargs.pop('clearable', True)
        super(FileField, self).__init__(*args, **kwargs)
        self._prefix = kwargs.get('_prefix', '')
        self.clear_field = fields.BooleanField(default=False)
        if self.clearable:
            self._clear_name = '%s-clear'%self.short_name
            self._clear_id = '%s-clear'%self.id
            self._clear = self.clear_field.bind(form=None, name=self._clear_name, prefix=self._prefix, id=self._clear_id)

    def process(self, formdata, data=fields._unset_value):
        super(FileField, self).process(formdata, data)
        if self.clearable:
            self._clear.process(formdata, data)
            self._clear.checked = False

    @property
    def clear(self):
        return (not self.clearable) or self._clear.data

    @property
    def data(self):
        data = self._data
        if data is not None:
            data.clear = self.clear
        return data

    @data.setter
    def data(self, data):
        self._data = data


class DatePickerWidget(widgets.TextInput):
    """
        Date picker widget.

        You must include bootstrap-datepicker.js and form.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'datepicker'
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class DateTimePickerWidget(widgets.TextInput):
    """
        Datetime picker widget.

        You must include bootstrap-datepicker.js and form.js for styling to work.
    """
    def __call__(self, field, **kwargs):
        kwargs['data-role'] = u'datetimepicker'
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)

# def format_form(form):
#     for field in form:
#         if isinstance(field,fields.SelectField):
#             field.widget = ChosenSelectWidget(multiple=field.widget.multiple)
#         elif isinstance(field, fields.DateTimeField):
#             field.widget = DatePickerWidget()
#         elif isinstance(field, fields.FormField):
#             format_form(field.form)
#     return form
#         # elif isinstance(field, fields.FieldList):
#         #     for f in field.entries: format_form
