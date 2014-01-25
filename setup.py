# Fix for older setuptools
import multiprocessing, logging, os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def desc():
    info = read('README.rst')
    try:
        return info + '\n\n' + read('doc/changelog.rst')
    except IOError:
        return info

setup(
    name='Flask-SuperAdmin',
    version='1.7.1',
    url='https://github.com/syrusakbary/flask-superadmin/',
    license='BSD',
    author='Syrus Akbary',
    author_email='me@syrusakbary.com',
    description='The best admin interface framework for Python. With scaffolding for MongoEngine, Django and SQLAlchemy.',
    long_description=desc(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.7',
        'Flask-WTF>=0.9'
    ],
    tests_require=[
        'nose>=1.0',
        'Flask',
        'flask-sqlalchemy',
        'django',
        'mongoengine'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    test_suite='nose.collector'
)
