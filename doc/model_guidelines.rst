Adding new model backend
========================

If you want to implement new database backend to use with model views, follow steps found in this guideline.

There are few assumptions about models:

    1. Model has "primary key" - value which uniquely identifies
       one model in a data store. There's no restriction on the
       data type or field name.
    2. Model has readable python properties
    3. It is possible to get list of models (optionally - sorted,
       filtered, etc) from data store
    4. It is possible to get one model by its primary key


Steps to add new model backend:

    1. Create new class and derive it from :class:`~flask_superadmin.model.base.BaseModelAdmin`::

        class MyDbModel(BaseModelView):
            pass

    By default, all model views accept model class and it
    will be stored as ``self.model``.

    2. **PLEASE VIEW** :class:`~flask_superadmin.model.backends.sqlalchemy.ModelAdmin` for how to do a new backend.

Feel free ask questions if you have problem adding new model backend.
