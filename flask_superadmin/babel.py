try:
    from flask.ext.babel import Domain

    from flask.ext.superadmin import translations

    class CustomDomain(Domain):
        def __init__(self):
            super(CustomDomain, self).__init__(translations.__path__[0],
                  domain='admin')

        def get_translations_path(self, ctx):
            print ctx

            dirname = ctx.app.extensions['admin'].translations_path
            if dirname is not None:
                return dirname

            return super(CustomDomain, self).get_translations_path(ctx)

    domain = CustomDomain()

    gettext = domain.gettext
    ngettext = domain.ngettext
    lazy_gettext = domain.lazy_gettext
except ImportError:
    def gettext(string, **variables):
        return string % variables

    def ngettext(singular, plural, num, **variables):
        return (singular if num == 1 else plural) % variables

    def lazy_gettext(string, **variables):
        return gettext(string, **variables)
