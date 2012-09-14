from flask_superadmin.form import BaseForm
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
        return isinstance(self.get_column(self.model, column), SORTABLE_FIELDS)

    def get_column(self, instance, name):
        return getattr(instance, name, None)

    def get_form(self, adding=False):
        return model_form(self.model,
                          BaseForm,
                          only=self.only,
                          exclude=self.exclude,
                          field_args=self.field_args,
                          converter=AdminModelConverter())

    def get_objects(self, *pks):
        return self.model.objects.in_bulk(list((ObjectId(pk) for pk in pks))) \
                                          .values()

    def get_object(self, pk):
        return self.model.objects.with_id(pk)

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
        query = self.model.objects

        #Select only the columns listed
        # cols = self.list_display
        # if cols:
        #     query = query.only(*cols)

        #Calculate number of rows
        count = query.count()

        #Order query
        if sort:
            query = query.order_by('%s%s' % ('-' if sort_desc else '', sort))

        # Pagination
        if page is not None:
            query = query.skip(page * self.list_per_page)
        query = query.limit(self.list_per_page)

        if execute:
            query = query.all()

        return count, query
