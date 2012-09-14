from flask_superadmin.model import ModelAdmin


def print_kwargs(d):
    return ', '.join(['%s=...' % k for k in d.keys()])


class DeprecatedModelView(object):
    def __init__(self, model, *args, **kwargs):
        import warnings
        msg = "The %s class is deprecated, use superadmin.model.ModelAdmin instead.\nOr just do admin.register(%s%s) for register your models."% (
            self.__class__.__name__,
            model.__name__,
            (', %s'%print_kwargs(kwargs) if kwargs else ''),
        )
        warnings.warn(msg, FutureWarning, stacklevel=2)
        super(DeprecatedModelView, self).__init__(model, *args, **kwargs)
