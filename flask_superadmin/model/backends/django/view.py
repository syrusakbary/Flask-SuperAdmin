from flask_superadmin.form import BaseForm
from flask_superadmin.model.base import BaseModelAdmin

from orm import model_form, AdminModelConverter
from django.db import models

class ModelAdmin(BaseModelAdmin):
    @staticmethod
    def model_detect(model):
        return issubclass(model, models.Model)

    def allow_pk(self):
        return False

    def get_column(self, instance, name):
        return self.get_column_value(getattr(instance, name, None))

    def get_form(self, adding=False):
        return model_form(self.model,
                          base_class=BaseForm,
                          only=self.only,
                          exclude=self.exclude,
                          field_args=self.field_args,
                          converter=AdminModelConverter())

    def get_queryset(self):
        return self.model.objects

    def get_objects(self, *pks):
        return self.get_queryset().filter(pk__in=pks)

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
        qs = self.get_queryset()

        #Calculate number of rows
        count = qs.count()

        #Order queryset
        if sort:
            qs = qs.order_by('%s%s' % ('-' if sort_desc else '', sort))

        # Pagination
        if page is not None:
            qs = qs.all()[page * self.list_per_page:]
        qs = qs[:self.list_per_page]

        if execute:
            qs = list(qs)

        return count, qs
