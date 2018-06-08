from pkg_resources import iter_entry_points


def init_extensions(app):
    """
    Load the Redash extensions for the given Redash Flask app.
    """
    if not hasattr(app, 'redash_extensions'):
        app.redash_extensions = {}

    if not hasattr(app, 'task_extensions'):
        app.task_extensions = {}

    for entry_point in iter_entry_points('redash.extensions'):
        app.logger.info('Loading Redash extension %s.', entry_point.name)
        extension = entry_point.load()
        extension_response = extension(app)
        extension_repository = app.redash_extensions

        # This is an interval task
        if (type(extension_response) == dict and
                "task" in extension_response and
                "interval_in_seconds" in extension_response):
            extension_repository = app.task_extensions

        extension_repository[entry_point.name] = extension_response
