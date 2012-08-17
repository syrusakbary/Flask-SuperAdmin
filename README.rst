Flask-SuperAdmin
================

The **best** admin interface framework for Flask. Better than Django admin.

With **scaffolding for Mongoengine, Django and SQLAlchemy**.


Screenshots
-----------

.. image:: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-list.png
    :width: 640
    :target: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-list.png

.. image:: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-edit.png
    :width: 640
    :target: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-list.png

Introduction
------------

This is library for building adminstrative interface on top of Flask framework.

Instead of providing simple scaffolding for SQLAlchemy, Mongoengine or Django models, Flask-SuperAdmin
provides tools that can be used to build adminstrative interface of any complexity,
using consistent look and feel.


Small example (Flask initialization omitted)::

    from flask.ext import superadmin

    app = Flask(__name__)
    admin = superadmin.Admin()

    # For SQLAlchemy
    from flask.ext.superadmin.contrib import sqlamodel
    admin.add_view(sqlamodel.ModelView(User, db.session)) # User is a SQLAlchemy Model, db.session is the session of our db

    # For Mongoengine Documents
    from flask.ext.superadmin.contrib import mongoenginemodel
    admin.add_view(mongoenginemodel.ModelView(User)) # User is a Mongoengine Document Model

    # For Django Models
    from flask.ext.superadmin.contrib import djangomodel
    admin.add_view(djangomodel.ModelView(User)) # User is a Django Document Model

    admin.add_view(GalleryManager(name='Photos', category='Cats'))
    admin.setup_app(app)

Examples
--------

Library comes with a lot of examples, you can find them in `examples <https://github.com/SyrusAkbary/Flask-SuperAdmin/tree/master/examples/>`_ directory.


Documentation
-------------

Flask-SuperAdmin is extensively documented, you can find `documentation here <http://readthedocs.org/docs/Flask-SuperAdmin>`_.

3rd Party Stuff
---------------

Flask-SuperAdmin is built with help of `Twitter Bootstrap <http://twitter.github.com/bootstrap/>`_, `Chosen <http://harvesthq.github.com/chosen/>`_, and `jQuery <http://jquery.com/>`_.


Kudos
-----

This library is a vitamined fork of the `Flask-Admin <https://github.com/mrjoes/flask-admin/>`_ package by Serge S. Koval.
