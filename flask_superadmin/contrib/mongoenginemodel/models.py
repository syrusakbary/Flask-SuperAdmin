from wtforms.form import Form


import mongoengine.fields as fields

def data_to_field (field,data):
    if isinstance(field,fields.EmbeddedDocumentField):
        return data_to_document(field.document_type_obj,data)
    elif isinstance(field,(fields.ListField, fields.SequenceField, fields.SortedListField)):
        l = []
        for d in data:
            l.append(data_to_field(field.field,d))
        return l
    elif isinstance(field,(fields.ReferenceField, fields.ObjectIdField)) and isinstance(data,basestring):
        from bson.objectid import ObjectId
        return ObjectId(data)
    else:
        return data

def data_to_document(document,data):
    from inspect import isclass
    new = document() if isclass(document) else document
    for name, value in data.iteritems():
        setattr(new,name,data_to_field(getattr(new.__class__,name),value))
    return new

class ModelForm(Form):
    def populate_obj(self, obj):
        return data_to_document(obj,self.data)