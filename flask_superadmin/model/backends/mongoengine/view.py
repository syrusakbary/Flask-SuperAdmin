from flask_superadmin.model.base import BaseModelAdmin

from .orm import model_form, AdminModelConverter

import operator
import mongoengine

from bson.objectid import ObjectId
from functools import reduce

SORTABLE_FIELDS = (
    mongoengine.BooleanField,
    mongoengine.DateTimeField,
    #mongoengine.DecimalField,
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

    def get_model_form(self):
        return model_form

    def get_converter(self):
        return AdminModelConverter

    def get_queryset(self):
        return self.model.objects

    def get_objects(self, *pks):
        return self.get_queryset().filter(pk__in=pks)

    def get_object(self, pk):
        return self.get_queryset().get(pk=pk)

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

    def construct_search(self, field_name):
        if field_name.startswith('^'):
            return "%s__istartswith" % field_name[1:]
        elif field_name.startswith('='):
            return "%s__iexact" % field_name[1:]
        else:
            return "%s__icontains" % field_name

    def get_list(self, page=0, sort=None, sort_desc=None, execute=False, search_query=None):
        qs = self.get_queryset()

        # Filter by search query
        if search_query and self.search_fields:
            orm_lookups = [self.construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in search_query.split():
                or_queries = [mongoengine.queryset.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                qs = qs.filter(reduce(operator.or_, or_queries))

        #Calculate number of documents
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

