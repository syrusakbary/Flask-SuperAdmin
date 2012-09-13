from flask_superadmin.form import BaseForm
from flask_superadmin.model.base import BaseModelAdmin

from orm import model_form, AdminModelConverter


class ModelAdmin(BaseModelAdmin):
    @staticmethod
    def model_detect(model):
        from django.db import models
        return issubclass(model, models.Model)

    def allow_pk(self):
        return False

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
        return self.model.objects.filter(pk__in=pks)

    def get_object(self, pk):
        return self.model.objects.get(pk=pk)

    def get_pk(self, instance):
        return str(instance.id)

    def save_model(self, instance, form, adding=False):
        form.populate_obj(instance)
        instance.save()
        return instance

    def delete_models(self, *pks):
        self.get_objects(*pks).delete()
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
            query = query.all()[page * self.list_per_page:]
        query = query[:self.list_per_page]

        if execute:
            query = list(query)

        return count, query
