from flask_superadmin.contrib import DeprecatedModelView

from flask_superadmin.model.backends.sqlalchemy import ModelAdmin


class ModelView(DeprecatedModelView, ModelAdmin):
    pass
