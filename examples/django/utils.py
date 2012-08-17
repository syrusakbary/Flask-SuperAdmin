def install_models(*all_models):
    from django.core.management.color import no_style
    from django.core.management.sql import custom_sql_for_model, emit_post_sync_signal
    from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
    db = 'default'
    connection = connections[db]
    cursor = connection.cursor()
    style = no_style()
    # Get a list of already installed *models* so that references work right.
    tables = connection.introspection.table_names()
    seen_models = connection.introspection.installed_models(tables)
    created_models = set()
    pending_references = {}
    def model_installed(model):
        opts = model._meta
        converter = connection.introspection.table_name_converter
        return not ((converter(opts.db_table) in tables) or
            (opts.auto_created and converter(opts.auto_created._meta.db_table) in tables))

    for model in all_models:
        sql, references = connection.creation.sql_create_model(model, style, seen_models)
        seen_models.add(model)
        created_models.add(model)
        for refto, refs in references.items():
            pending_references.setdefault(refto, []).extend(refs)
            if refto in seen_models:
                sql.extend(connection.creation.sql_for_pending_references(refto, style, pending_references))
        sql.extend(connection.creation.sql_for_pending_references(model, style, pending_references))
        for statement in sql:
            cursor.execute(statement)
        tables.append(connection.introspection.table_name_converter(model._meta.db_table))

    transaction.commit_unless_managed(using=db)
