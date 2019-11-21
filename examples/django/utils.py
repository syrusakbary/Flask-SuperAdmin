def install_models(*all_models):
    from django.db import connection

    for model in all_models:
        with connection.schema_editor() as editor:
            editor.create_model(model)
