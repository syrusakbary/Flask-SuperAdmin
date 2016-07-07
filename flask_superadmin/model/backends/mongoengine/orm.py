"""
Tools for generating forms based on MongoEngine Document schemas.
"""

import inspect
from werkzeug import secure_filename
from wtforms import Form, validators, fields as f

from .fields import ModelSelectField, ModelSelectMultipleField, ListField
from mongoengine.fields import ReferenceField, IntField, FloatField

from flask_superadmin.model import AdminModelConverter as AdminModelConverter_

__all__ = ('model_fields', 'model_form')


def converts(*args):
    """ A convenient decorator for the ModelConverter used to mark which
    method should be used to convert which MongoEngine field.
    """
    def _inner(func):
        func._converter_for = frozenset(args)
        return func
    return _inner


class ModelConverter(object):
    """ Manages the way MongoEngine fields are converted into WTForms fields
    """
    def __init__(self, converters=None):

        if not converters:
            converters = {}

        for name in dir(self):
            obj = getattr(self, name)
            if hasattr(obj, '_converter_for'):
                for classname in obj._converter_for:
                    converters[classname] = obj

        self.converters = converters

    def convert(self, model, field, field_args, multiple=False):
        kwargs = {
            'label': str(field.verbose_name or field.name or ''),
            'description': field.help_text or '',
            'validators': [],
            'filters': [],
            'default': field.default,
        }
        if field_args:
            kwargs.update(field_args)

        if field.required:

            # Hacky but necessary, since validators.Required doesn't handle 0 properly
            if isinstance(field, IntField) or isinstance(field, FloatField):
                kwargs['validators'].append(validators.InputRequired())
            else:
                kwargs['validators'].append(validators.Required())
        else:
            kwargs['validators'].append(validators.Optional())

        if field.choices:
            kwargs['choices'] = field.choices
            if isinstance(field, IntField):
                kwargs['coerce'] = int
            if not multiple:
                return f.SelectField(**kwargs)
            else:
                return f.SelectMultipleField(**kwargs)
        ftype = type(field).__name__

        if hasattr(field, 'to_form_field'):
            return field.to_form_field(model, kwargs)

        if ftype in self.converters:
            return self.converters[ftype](model, field, kwargs)

    @classmethod
    def _string_common(cls, model, field, kwargs):
        if field.max_length or field.min_length:
            kwargs['validators'].append(
                validators.Length(max=field.max_length or - 1,
                                  min=field.min_length or - 1))

    @classmethod
    def _number_common(cls, model, field, kwargs):
        if field.max_value or field.min_value:
            kwargs['validators'].append(
                validators.NumberRange(max=field.max_value,
                                       min=field.min_value))

    @converts('StringField')
    def conv_String(self, model, field, kwargs):
        if field.regex:
            kwargs['validators'].append(validators.Regexp(regex=field.regex))
        self._string_common(model, field, kwargs)
        if field.max_length:
            return f.TextField(**kwargs)
        return f.TextAreaField(**kwargs)

    @converts('URLField')
    def conv_URL(self, model, field, kwargs):
        kwargs['validators'].append(validators.URL())
        self._string_common(model, field, kwargs)
        return f.TextField(**kwargs)

    @converts('EmailField')
    def conv_Email(self, model, field, kwargs):
        kwargs['validators'].append(validators.Email())
        self._string_common(model, field, kwargs)
        return f.TextField(**kwargs)

    @converts('IntField')
    def conv_Int(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.IntegerField(**kwargs)

    @converts('FloatField')
    def conv_Float(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.FloatField(**kwargs)

    @converts('FileField')
    def conv_File(self, model, field, kwargs):
        return f.FileField(**kwargs)

    @converts('ImageField')
    def conv_Image(self, model, field, kwargs):
        return f.FileField(**kwargs)

    @converts('DecimalField')
    def conv_Decimal(self, model, field, kwargs):
        self._number_common(model, field, kwargs)
        return f.DecimalField(**kwargs)

    @converts('BooleanField')
    def conv_Boolean(self, model, field, kwargs):
        return f.BooleanField(**kwargs)

    @converts('DateTimeField')
    def conv_DateTime(self, model, field, kwargs):
        # kwargs['widget'] = form.DateTimePickerWidget()
        return f.DateTimeField(**kwargs)

    @converts('BinaryField')
    def conv_Binary(self, model, field, kwargs):
        #TODO: may be set file field that will save file`s data to MongoDB
        if field.max_bytes:
            kwargs['validators'].append(validators.Length(max=field.max_bytes))
        return f.TextAreaField(**kwargs)

    @converts('DictField')
    def conv_Dict(self, model, field, kwargs):
        return f.TextAreaField(**kwargs)

    @converts('ListField')
    def conv_List(self, model, field, kwargs):
        kwargs = kwargs or {
            'validators': [],
            'filters': [],
            'label': str(field.verbose_name or field.name or ''),
        }
        if field.field.choices:
            return self.convert(model, field.field, None, multiple=True)
        if isinstance(field.field, ReferenceField):
            return ModelSelectMultipleField(model=field.field.document_type, **kwargs)
        unbound_field = self.convert(model, field.field, {})
        return ListField(unbound_field, min_entries=0, **kwargs)

    @converts('SortedListField')
    def conv_SortedList(self, model, field, kwargs):
        #TODO: sort functionality, may be need sortable widget
        return self.conv_List(model, field, kwargs)

    @converts('GeoLocationField')
    def conv_GeoLocation(self, model, field, kwargs):
        #TODO: create geo field and widget (also GoogleMaps)
        return

    @converts('ObjectIdField')
    def conv_ObjectId(self, model, field, kwargs):
        return

    @converts('EmbeddedDocumentField')
    def conv_EmbeddedDocument(self, model, field, kwargs):
        kwargs = {
            'validators': [],
            'filters': [],
        }
        form_class = model_form(field.document_type_obj, field_args={},
                                converter=self)
        return f.FormField(form_class, **kwargs)

    @converts('ReferenceField')
    def conv_Reference(self, model, field, kwargs):
        kwargs['allow_blank'] = not field.required
        return ModelSelectField(model=field.document_type, **kwargs)

    @converts('GenericReferenceField')
    def conv_GenericReference(self, model, field, kwargs):
        return


def model_fields(model, fields=None, readonly_fields=None, exclude=None,
                 field_args=None, converter=None):
    """
    Generate a dictionary of WTForms fields for a given MongoEngine model.

    See `model_form` docstring for description of parameters.
    """
    from mongoengine.base import BaseDocument
    if BaseDocument not in inspect.getmro(model):
        raise TypeError('Model must be a MongoEngine Document schema')

    readonly_fields = readonly_fields or []
    exclude = exclude or []

    converter = converter or ModelConverter()
    field_args = field_args or {}

    field_names = fields if fields else list(model._fields.keys())
    field_names = (x for x in field_names if x not in exclude)

    field_dict = {}
    for name in field_names:
        if name not in readonly_fields and name not in model._fields:
            raise KeyError('"%s" is not read-only and does not appear to be a field on the document.' % name)

        if name in model._fields and name not in readonly_fields:
            model_field = model._fields[name]
            field = converter.convert(model, model_field, field_args.get(name))
            if field is not None:
                field_dict[name] = field

    return field_dict


import mongoengine.fields as fields

_unset_value = object()
_remove_file_value = object()

def data_to_field(field, data):
    if isinstance(field, fields.EmbeddedDocumentField):
        return data_to_document(field.document_type_obj, data)
    elif isinstance(field, (fields.ListField, fields.SequenceField,
                    fields.SortedListField)):
        l = []
        for d in data:
            l.append(data_to_field(field.field, d))
        return l
    elif isinstance(field, (fields.FileField)):
        if data.filename:
            gfs = field.proxy_class(
                        db_alias=field.db_alias,
                        collection_name=field.collection_name,
                        instance=field.owner_document(),
                        key=field.name)
            gfs.put(data.stream, filename=secure_filename(data.filename), content_type=data.mimetype)
            return gfs
        elif data.clear:
            return _remove_file_value
        return _unset_value
    elif isinstance(field, (fields.ReferenceField, fields.ObjectIdField)) and \
                    isinstance(data, str):
        from bson.objectid import ObjectId
        return ObjectId(data)
    else:
        return data


def data_to_document(document, data):
    from inspect import isclass
    new = document() if isclass(document) else document
    for name, value in data.items():
        field = getattr(new.__class__, name)
        field_value = data_to_field(field, value)
        if field_value != _unset_value:
            if field_value == _remove_file_value:
                getattr(new, name).delete()
            else:
                setattr(new, name, field_value)
    return new


def model_form(model, base_class=Form, fields=None, readonly_fields=None,
               exclude=None, field_args=None, converter=None):
    """
    Create a wtforms Form for a given MongoEngine Document schema::

        from flaskext.mongoengine.wtf import model_form
        from myproject.myapp.schemas import Article
        ArticleForm = model_form(Article)

    :param model:
        A MongoEngine Document schema class
    :param base_class:
        Base form class to extend from. Must be a ``wtforms.Form`` subclass.
    :param fields:
        An optional iterable with the property names that should be included
        in the form. Only these properties will have fields. It also
        determines the order of the fields.
    :param exclude:
        An optional iterable with the property names that should be excluded
        from the form. All other properties will have fields.
    :param field_args:
        An optional dictionary of field names mapping to keyword arguments used
        to construct each field object.
    :param converter:
        A converter to generate the fields based on the model properties. If
        not set, ``ModelConverter`` is used.
    """
    field_dict = model_fields(model, fields, readonly_fields, exclude,
                              field_args, converter)
    field_dict['model_class'] = model

    def populate_obj(self, obj):
        return data_to_document(obj, self.data)

    field_dict['populate_obj'] = populate_obj

    return type(model.__name__ + 'Form', (base_class,), field_dict)


class AdminModelConverter(AdminModelConverter_, ModelConverter):
    pass

