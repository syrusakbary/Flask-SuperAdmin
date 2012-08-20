from flask import flash

from flask.ext.superadmin.babel import gettext
from flask.ext.superadmin.form import BaseForm
from flask.ext.superadmin.model import BaseModelView

from flask.ext.superadmin.contrib.mongoenginemodel import orm as form #, filters, tools

import mongoengine

class ModelView(BaseModelView):
    """
        Mongoengine model view

        Usage sample::

            admin = Admin()
            admin.add_view(ModelView(User))
    """

    # hide_backrefs = True
    # """
    #     Set this to False if you want to see multiselect for model backrefs.
    # """

    # auto_select_related = True
    # """
    #     Enable automatic detection of displayed foreign keys in this view
    #     and perform automatic joined loading for related models to improve
    #     query performance.

    #     Please note that detection is not recursive: if `__unicode__` method
    #     of related model uses another model to generate string representation, it
    #     will still make separate database call.
    # """
    list_display = []
    list_select_related = None
    """
        List of parameters for SQLAlchemy `subqueryload`. Overrides `auto_select_related`
        property.

        For example::

            class PostAdmin(ModelAdmin):
                list_select_related = ('user', 'city')

        You can also use properties::

            class PostAdmin(ModelAdmin):
                list_select_related = (Post.user, Post.city)

        Please refer to the `subqueryload` on list of possible values.
    """

    searchable_columns = None
    """
        Collection of the searchable columns. Only text-based columns
        are searchable (`String`, `Unicode`, `Text`, `UnicodeText`).

        Example::

            class MyModelView(ModelView):
                searchable_columns = ('name', 'email')

        You can also pass columns::

            class MyModelView(ModelView):
                searchable_columns = (User.name, User.email)

        Following search rules apply:

        - If you enter *ZZZ* in the UI search field, it will generate *ILIKE '%ZZZ%'*
          statement against searchable columns.

        - If you enter multiple words, each word will be searched separately, but
          only rows that contain all words will be displayed. For example, searching
          for 'abc def' will find all rows that contain 'abc' and 'def' in one or
          more columns.

        - If you prefix your search term with ^, it will find all rows
          that start with ^. So, if you entered *^ZZZ*, *ILIKE 'ZZZ%'* will be used.

        - If you prefix your search term with =, it will do exact match.
          For example, if you entered *=ZZZ*, *ILIKE 'ZZZ'* statement will be used.
    """

    # column_filters = None
    # """
    #     Collection of the column filters.

    #     Can contain either field names or instances of :class:`flask.ext.superadmin.contrib.sqlamodel.filters.BaseFilter` classes.

    #     For example::

    #         class MyModelView(BaseModelView):
    #             column_filters = ('user', 'email')

    #     or::

    #         class MyModelView(BaseModelView):
    #             column_filters = (BooleanEqualFilter(User.name, 'Name'))
    # """

    # filter_converter = filters.FilterConverter()
    # """
    #     Field to filter converter.

    #     Override this attribute to use non-default converter.
    # """

    def __init__(self, model, 
                 name=None, category=None, endpoint=None, url=None):
        """
            Constructor.

            `model`
                Model class
            `name`
                View name. If not set, will default to model name
            `category`
                Category name
            `endpoint`
                Endpoint name. If not set, will default to model name
            `url`
                Base URL. If not set, will default to '/admin/' + endpoint
        """
        self._search_fields = None
        self._search_joins = dict()

        self._filter_joins = dict()

        super(ModelView, self).__init__(model, name, category, endpoint, url)

        # Primary key
        self._primary_key = self.scaffold_pk()

        # Configuration
        # if not self.list_select_related:
        #     self._auto_joins = self.scaffold_auto_joins()
        # else:
        #     self._auto_joins = self.list_select_related


    # Scaffolding
    def scaffold_pk(self):
        """
            Return primary key name from a model
        """
        return 'pk'

    def get_pk_value(self, model):
        """
            Return PK value from a model object.
        """
        return getattr(model, self._primary_key)

    def scaffold_list_columns(self):
        """
            Return list of columns from the model.
        """
        columns = []
        printable = (
            mongoengine.fields.BinaryField,
            mongoengine.fields.DecimalField,
            mongoengine.fields.ReferenceField,
            mongoengine.fields.FloatField,
            mongoengine.fields.DateTimeField,
            mongoengine.fields.ObjectIdField,
            mongoengine.fields.URLField,
            mongoengine.fields.DictField,
            mongoengine.fields.IntField,
            mongoengine.fields.EmailField,
            mongoengine.fields.ComplexDateTimeField,
            mongoengine.fields.GeoPointField,
            mongoengine.fields.UUIDField,
            mongoengine.fields.StringField
        )
        for name,field in self.list_display:
            if name=='id':continue
            if isinstance(field,printable): columns.append(name)
        return columns

    def scaffold_sortable_columns(self):
        """
            Return dictionary of sortable columns.
            Key is column name, value is sort column/field.
        """
        columns = dict()

        for k,v in self.model._fields.items():
            columns[k] = k

        return columns

    # def _get_columns_for_field(self, field):
    #     if isinstance(field, basestring):
    #         attr = getattr(self.model, field, None)

    #         if field is None:
    #             raise Exception('Field %s was not found.' % field)
    #     else:
    #         attr = field

    #     if (not attr or
    #         not hasattr(attr, 'property') or
    #         not hasattr(attr.property, 'columns') or
    #         not attr.property.columns):
    #             raise Exception('Invalid field %s: does not contains any columns.' % field)

    #     return attr.property.columns

    # def init_search(self):
    #     """
    #         Initialize search. Returns `True` if search is supported for this
    #         view.

    #         For SQLAlchemy, this will initialize internal fields: list of
    #         column objects used for filtering, etc.
    #     """
    #     if self.searchable_columns:
    #         self._search_fields = []
    #         self._search_joins = dict()

    #         for p in self.searchable_columns:
    #             for column in self._get_columns_for_field(p):
    #                 column_type = type(column.type).__name__

    #                 if not self.is_text_column_type(column_type):
    #                     raise Exception('Can only search on text columns. ' +
    #                                     'Failed to setup search for "%s"' % p)

    #                 self._search_fields.append(column)

    #                 # If it belongs to different table - add a join
    #                 if column.table != self.model.__table__:
    #                     self._search_joins[column.table.name] = column.table

    #     return bool(self.searchable_columns)

    # def is_text_column_type(self, name):
    #     """
    #         Verify if column type is text-based.

    #         Returns `True` for `String`, `Unicode`, `Text`, `UnicodeText`
    #     """
    #     return (name == 'String' or name == 'Unicode' or
    #             name == 'Text' or name == 'UnicodeText')

    def scaffold_filters(self, name):
        if isinstance(name, basestring):
            attr = getattr(self.model, name, None)
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        if hasattr(attr, 'property') and hasattr(attr.property, 'direction'):
            filters = []

            for p in self._get_model_iterator(attr.property.mapper.class_):
                if hasattr(p, 'columns'):
                    # TODO: Check for multiple columns
                    column = p.columns[0]

                    if column.foreign_keys or column.primary_key:
                        continue

                    visible_name = '%s / %s' % (self.get_column_name(attr.prop.table.name),
                                                self.get_column_name(p.key))

                    type_name = type(column.type).__name__
                    flt = self.filter_converter.convert(type_name,
                                                        column,
                                                        visible_name)

                    if flt:
                        self._filter_joins[column.table.name] = column.table
                        filters.extend(flt)

            return filters
        else:
            columns = self._get_columns_for_field(attr)

            if len(columns) > 1:
                raise Exception('Can not filter more than on one column for %s' % name)

            column = columns[0]

            if not isinstance(name, basestring):
                visible_name = self.get_column_name(name.property.key)
            else:
                visible_name = self.get_column_name(name)

            type_name = type(column.type).__name__
            flt = self.filter_converter.convert(type_name,
                                                column,
                                                visible_name)

            if flt:
                # If there's relation to other table, do it
                if column.table != self.model.__table__:
                    self._filter_joins[column.table.name] = column.table

            return flt

    def is_valid_filter(self, filter):
        """
            Verify that provided filter object is derived from the
            SQLAlchemy-compatible filter class.

            `filter`
                Filter object to verify.
        """
        return isinstance(filter, filters.BaseSQLAFilter)

    def scaffold_form(self):
        """
            Create form from the model.
        """
        return form.model_form(self.model,
                          BaseForm,
                          only=self.form_columns,
                          exclude=self.excluded_form_columns,
                          field_args=self.form_args,
                          converter=form.AdminModelConverter())

    # Database-related API
    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True):
        """
            Return models from the database.

            `page`
                Page number
            `sort_column`
                Sort column name
            `sort_desc`
                Descending or ascending sort
            `search`
                Search query
            `execute`
                Execute query immediately? Default is `True`
            `filters`
                List of filter tuples
        """
        
        query = self.model.objects
        #Select only the columns listed
        cols = self.scaffold_list_columns()
        if cols:
            query = query.only(*cols)
        #Calculate number of rows
        count = query.count()
        #Order query
        if sort_column:
            query = query.order_by('%s%s'% ('-' if sort_desc else'', sort_column))
        
        # Pagination
        if page is not None:
            query = query.skip(page * self.page_size)
        query = query.limit(self.page_size)

        if execute:
            query = query.all()
        return count,query
        # Apply search criteria
        # if self._search_supported and search:
        #     # Apply search-related joins
        #     if self._search_joins:
        #         query = query.join(*self._search_joins.values())
        #         joins = set(self._search_joins.keys())

        #     # Apply terms
        #     terms = search.split(' ')

        #     for term in terms:
        #         if not term:
        #             continue

        #         stmt = tools.parse_like_term(term)
        #         filter_stmt = [c.ilike(stmt) for c in self._search_fields]
        #         query = query.filter(or_(*filter_stmt))

        # # Apply filters
        # if self._filters:
        #     # Apply search-related joins
        #     if self._filter_joins:
        #         new_joins = set(self._filter_joins.keys()) - joins

        #         if new_joins:
        #             query = query.join(*[self._filter_joins[jn] for jn in new_joins])
        #             joins |= new_joins

        #     # Apply filters
        #     for flt, value in filters:
        #         query = self._filters[flt].apply(query, value)

        # # Calculate number of rows
        # count = query.count()

        # # Auto join
        # for j in self._auto_joins:
        #     query = query.options(subqueryload(j))

        # # Sorting
        # if sort_column is not None:
        #     if sort_column in self._sortable_columns:
        #         sort_field = self._sortable_columns[sort_column]

        #         # Try to handle it as a string
        #         if isinstance(sort_field, basestring):
        #             # Create automatic join against a table if column name
        #             # contains dot.
        #             if '.' in sort_field:
        #                 parts = sort_field.split('.', 1)

        #                 if parts[0] not in joins:
        #                     query = query.join(parts[0])
        #                     joins.add(parts[0])
        #         elif isinstance(sort_field, InstrumentedAttribute):
        #             table = sort_field.parententity.tables[0]

        #             if table.name not in joins:
        #                 query = query.join(table)
        #                 joins.add(table.name)
        #         elif isinstance(sort_field, Column):
        #             pass
        #         else:
        #             raise TypeError('Wrong argument type')

        #         if sort_field is not None:
        #             if sort_desc:
        #                 query = query.order_by(desc(sort_field))
        #             else:
        #                 query = query.order_by(sort_field)

        # # Pagination
        # if page is not None:
        #     query = query.offset(page * self.page_size)

        # query = query.limit(self.page_size)

        # # Execute if needed
        # if execute:
        #     query = query.all()

        return count, query

    def get_one(self, id):
        """
            Return one model by its id.

            `id`
                Model
        """
        return self.model.objects.with_id(id)

    # Model handlers
    def create_model(self, form):
        """
            Create model from form.

            `form`
                Form instance
        """
        try:
            model = self.model()
            form.populate_obj(model)
            model.save()            
            return True
        except Exception, ex:
            flash(gettext('Failed to create model. %(error)s', error=str(ex)), 'error')
            return False

    def update_model(self, form, model):
        """
            Update model from form.

            `form`
                Form instance
        """
        try:
            # print '*******',form.data, model
            form.populate_obj(model)
            # print model.to_mongo()
            model.save()
            return True
        except Exception, ex:
            flash(gettext('Failed to update model. %(error)s', error=str(ex)), 'error')
            return False

    def delete_model(self, model):
        """
            Delete model.

            `model`
                Model to delete
        """
        try:
            model.delete()
            return True
        except Exception, ex:
            flash(gettext('Failed to delete model. %(error)s', error=str(ex)), 'error')
            return False
