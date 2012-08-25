Flask-SuperAdmin
================

Flask-Superadmin is the **best** admin interface framework for `Flask <http://flask.pocoo.org/>`_. As good as Django admin.

Batteries included:

* Admin interface
* **Scaffolding for MongoEngine, Django and SQLAlchemy**
* File administrator (optional)

Requirements:

* `Flask`_
* `WTForms <https://bitbucket.org/simplecodes/wtforms>`_


Admin interface
---------------

Influenced heavily by the Django admin, **provides easy create/edit/delete functionality** for your 
project's models (MongoEngine, Django or SQLAlchemy).


.. image:: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-list.png
    :width: 640px
    :target: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-list.png

.. image:: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-edit.png
    :width: 640px
    :target: https://raw.github.com/SyrusAkbary/Flask-SuperAdmin/master/screenshots/model-edit.png


Introduction
------------

This is library for building adminstrative interface on top of Flask framework.

Instead of providing simple scaffolding for SQLAlchemy, Mongoengine or Django models, Flask-SuperAdmin
provides tools that can be used to build adminstrative interface of any complexity,
using consistent look and feel.


Small example (Flask initialization omitted)::

    from flask.ext.superadmin import Admin, model

    app = Flask(__name__)
    admin = Admin(app)

    # For SQLAlchemy (User is a SQLAlchemy Model/Table)
    admin.register(User, session=db.session) 

    # For Mongoengine Documents (User is a MongoEngine Document)
    admin.register(User)

    # For Django Models (User is a Django Model)
    admin.register(User)

    admin.add_view(CustomView(name='Photos', category='Cats'))
    admin.setup_app(app)


Installation
------------

For installing you have to do::

    pip install Flask-SuperAdmin

Or::

    python setup.py install


Examples
--------

Library comes with a lot of examples, you can find them in `examples <https://github.com/SyrusAkbary/Flask-SuperAdmin/tree/master/examples/>`_ directory.


Documentation
-------------

Flask-SuperAdmin is extensively documented, you can find `documentation here <http://flask-superadmin.readthedocs.org/>`_.


3rd Party Stuff
---------------

Flask-SuperAdmin is built with help of `Twitter Bootstrap <http://twitter.github.com/bootstrap/>`_, `Chosen <http://harvesthq.github.com/chosen/>`_, and `jQuery <http://jquery.com/>`_.


Kudos
-----

This library is a supervitamined fork of the `Flask-Admin <https://github.com/mrjoes/flask-admin/>`_ package by Serge S. Koval.
