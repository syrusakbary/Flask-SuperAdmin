from sqlalchemy.sql.expression import desc, literal

from orm import model_form, AdminModelConverter

from flask_superadmin.model.base import BaseModelAdmin
from sqlalchemy import schema


class ModelAdmin(BaseModelAdmin):
    hide_backrefs = False

    def __init__(self, model, session=None,
                 *args, **kwargs):
        super(ModelAdmin, self).__init__(model, *args, **kwargs)
        if session:
            self.session = session
        self._primary_key = self.pk_key

    @staticmethod
    def model_detect(model):
        return isinstance(getattr(model, 'metadata', None), schema.MetaData)

    def _get_model_iterator(self, model=None):
        """
            Return property iterator for the model
        """
        if model is None:
            model = self.model

        return model._sa_class_manager.mapper.iterate_properties

    @property
    def pk_key(self):
        for p in self._get_model_iterator():
            if hasattr(p, 'columns'):
                for c in p.columns:
                    if c.primary_key:
                        return p.key

    def allow_pk(self):
        return False

    def get_model_form(self):
        return model_form

    def get_converter(self):
        return AdminModelConverter(self)

    @property
    def query(self):
        return self.get_queryset()  # TODO remove eventually (kept for backwards compatibility)

    def get_queryset(self):
        return self.session.query(self.model)

    def get_objects(self, *pks):
        id = self.get_pk(self.model)
        return self.get_queryset().filter(id.in_(pks))

    def get_object(self, pk):
        return self.get_queryset().get(pk)

    def get_pk(self, instance):
        return getattr(instance, self._primary_key)

    def save_model(self, instance, form, adding=False):
        form.populate_obj(instance)
        if adding:
            self.session.add(instance)
        self.session.commit()
        return instance

    def delete_models(self, *pks):
        objs = self.get_objects(*pks)
        objs.delete(synchronize_session='fetch')
        self.session.commit()
        return True

    def construct_search(self, field_name):
        if field_name.startswith('^'):
            return literal(field_name[1:]).startswith
        elif field_name.startswith('='):
            return literal(field_name[1:]).op('=')
        else:
            return literal(field_name).contains

    def get_list(self, page=0, sort=None, sort_desc=None, execute=False, search_query=None):
        qs = self.get_queryset()

        # Filter by search query
        if search_query and self.search_fields:
            orm_lookups = [self.construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in search_query.split():
                or_queries = [orm_lookup(bit) for orm_lookup in orm_lookups]
                qs = qs.filter(sum(or_queries))

        count = qs.count()

        #Order queryset
        if sort:
            if sort_desc:
                sort = desc(sort)
            qs = qs.order_by(sort)

        # Pagination
        if page is not None:
            qs = qs.offset(page * self.list_per_page)

        qs = qs.limit(self.list_per_page)

        if execute:
            qs = qs.all()

        return count, qs

