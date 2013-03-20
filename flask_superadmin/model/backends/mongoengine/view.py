from flask_superadmin.model.base import BaseModelAdmin

from orm import model_form, AdminModelConverter

import mongoengine

from bson.objectid import ObjectId

SORTABLE_FIELDS = (
    mongoengine.BooleanField,
    mongoengine.DateTimeField,
    mongoengine.DecimalField,
    mongoengine.FloatField,
    mongoengine.IntField,
    mongoengine.StringField,
    mongoengine.ReferenceField
)


class ModelAdmin(BaseModelAdmin):
    @staticmethod
    def model_detect(model):
        return issubclass(model, mongoengine.Document)

    def allow_pk(self):
        return False

    def is_sortable(self, column):
        field = getattr(self.model, column, None)
        return isinstance(field, SORTABLE_FIELDS)

    def get_column(self, instance, name):
        value = getattr(instance, name, None)
        field = instance._fields.get(name, None)
        if field and field.choices:
            choices = dict(field.choices)
            if value in choices: return choices[value]
        return self.get_column_value(value)

    def get_model_form(self):
        return model_form

    def get_converter(self):
        return AdminModelConverter

    def get_queryset(self):
        return self.model.objects

    def get_objects(self, *pks):
        return self.get_queryset().in_bulk(list((ObjectId(pk) for pk in pks))) \
                                          .values()

    def get_object(self, pk):
        return self.get_queryset().with_id(pk)

    def get_pk(self, instance):
        return str(instance.id)

    def save_model(self, instance, form, adding=False):
        form.populate_obj(instance)
        instance.save()
        return instance

    def delete_models(self, *pks):
        for obj in self.get_objects(*pks):
            obj.delete()
        return True

    def get_list(self, page=0, sort=None, sort_desc=None, execute=False):
        qs = self.get_queryset()

        #Calculate number of rows
        count = qs.count()

        #Order queryset
        if sort:
            qs = qs.order_by('%s%s' % ('-' if sort_desc else '', sort))

        # Pagination
        if page is not None:
            qs = qs.skip(page * self.list_per_page)
        qs = qs.limit(self.list_per_page)

        if execute:
            qs = qs.all()

        return count, qs
