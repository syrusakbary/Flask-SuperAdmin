import os
import os.path as op
import platform
import urlparse
import re
import shutil

from operator import itemgetter

from werkzeug import secure_filename

from flask import flash, url_for, redirect, abort, request

from flask_superadmin.base import BaseView, expose
from flask_superadmin.babel import gettext, lazy_gettext
from flask_superadmin import form
from flask_wtf.file import FileField
from wtforms import StringField, ValidationError


class NameForm(form.BaseForm):
    """
        Form with a filename input field.

        Validates if provided name is valid for *nix and Windows systems.
    """
    name = StringField()

    regexp = re.compile(r'^(?!^(PRN|AUX|CLOCK\$|NUL|CON|COM\d|LPT\d|\..*)'
                        r'(\..+)?$)[^\x00-\x1f\\?*:\";|/]+$')

    def validate_name(self, field):
        if not self.regexp.match(field.data):
            raise ValidationError(gettext('Invalid directory name'))


class UploadForm(form.BaseForm):
    """
        File upload form. Works with FileAdmin instance to check if it
        is allowed to upload file with given extension.
    """
    upload = FileField(lazy_gettext('File to upload'))

    def __init__(self, admin):
        self.admin = admin

        super(UploadForm, self).__init__()

    def validate_upload(self, field):
        if not self.upload.has_file():
            raise ValidationError(gettext('File required.'))

        filename = self.upload.data.filename

        if not self.admin.is_file_allowed(filename):
            raise ValidationError(gettext('Invalid file type.'))


class FileAdmin(BaseView):
    """
        Simple file-management interface.

        Requires two parameters:

        `path`
            Path to the directory which will be managed
        `url`
            Base URL for the directory. Will be used to generate
            static links to the files.

        Sample usage::

            admin = Admin()

            path = op.join(op.dirname(__file__), 'static')
            admin.add_view(FileAdmin(path, '/static/', name='Static Files'))
            admin.setup_app(app)
    """

    can_upload = True
    """
        Is file upload allowed.
    """

    can_delete = True
    """
        Is file deletion allowed.
    """

    can_delete_dirs = True
    """
        Is recursive directory deletion is allowed.
    """

    can_mkdir = True
    """
        Is directory creation allowed.
    """

    can_rename = True
    """
        Is file and directory renaming allowed.
    """

    allowed_extensions = None
    """
        List of allowed extensions for uploads, in lower case.

        Example::

            class MyAdmin(FileAdmin):
                allowed_extensions = ('swf', 'jpg', 'gif', 'png')
    """

    list_template = 'admin/file/list.html'
    """
        File list template
    """

    upload_template = 'admin/file/form.html'
    """
        File upload template
    """

    mkdir_template = 'admin/file/form.html'
    """
        Directory creation (mkdir) template
    """

    rename_template = 'admin/file/rename.html'
    """
        Rename template
    """

    def __init__(self, base_path, base_url,
                 name=None, category=None, endpoint=None, url=None):
        """
            Constructor.

            `base_path`
                Base file storage location
            `base_url`
                Base URL for the files
            `name`
                Name of this view. If not provided,
                will be defaulted to the class name.
            `category`
                View category
            `endpoint`
                Endpoint name for the view
            `url`
                URL for view
        """
        self.base_path = base_path
        self.base_url = base_url

        self._on_windows = platform.system() == 'Windows'

        # Convert allowed_extensions to set for quick validation
        if (self.allowed_extensions
                and not isinstance(self.allowed_extensions, set)):
            self.allowed_extensions = set(self.allowed_extensions)

        super(FileAdmin, self).__init__(name, category, endpoint, url)

    def is_accessible_path(self, path):
        """
            Verify if path is accessible for current user.

            Override to customize behavior.

            `path`
                Relative path to the root
        """
        return True

    def get_base_path(self):
        """
            Return base path. Override to customize behavior (per-user
            directories, etc)
        """
        return op.normpath(self.base_path)

    def get_base_url(self):
        """
            Return base URL. Override to customize behavior (per-user
            directories, etc)
        """
        return self.base_url

    def is_file_allowed(self, filename):
        """
            Verify if file can be uploaded.

            Override to customize behavior.

            `filename`
                Source file name
        """
        ext = op.splitext(filename)[1].lower()

        if ext.startswith('.'):
            ext = ext[1:]

        if self.allowed_extensions and ext not in self.allowed_extensions:
            return False

        return True

    def is_in_folder(self, base_path, directory):
        """
            Verify if `directory` is in `base_path` folder
        """
        return op.normpath(directory).startswith(base_path)

    def save_file(self, path, file_data):
        """
            Save uploaded file to the disk

            `path`
                Path to save to
            `file_data`
                Werkzeug `FileStorage` object
        """
        file_data.save(path)

    def _get_dir_url(self, endpoint, path, **kwargs):
        """
            Return prettified URL

            `endpoint`
                Endpoint name
            `path`
                Directory path
            `kwargs`
                Additional arguments
        """
        if not path:
            return url_for(endpoint)
        else:
            if self._on_windows:
                path = path.replace('\\', '/')

            kwargs['path'] = path

            return url_for(endpoint, **kwargs)

    def _get_file_url(self, path):
        """
            Return static file url

            `path`
                Static file path
        """
        base_url = self.get_base_url()
        return urlparse.urljoin(base_url, path)

    def _normalize_path(self, path):
        """
            Verify and normalize path.

            If path is not relative to the base directory,
            will throw 404 exception.

            If path does not exist, will also throw 404 exception.
        """
        base_path = self.get_base_path()

        if path is None:
            directory = base_path
            path = ''
        else:
            path = op.normpath(path)
            directory = op.normpath(op.join(base_path, path))

            if not self.is_in_folder(base_path, directory):
                abort(404)

        if not op.exists(directory):
            abort(404)

        return base_path, directory, path

    def field_name(self, text):
        return text.capitalize()

    def get_readonly_fields(self, instance):
        return {}

    @expose('/')
    @expose('/b/<path:path>')
    def index(self, path=None):
        """
            Index view method

            `path`
                Optional directory path. If not provided,
                will use base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        # Get directory listing
        items = []

        # Parent directory
        if directory != base_path:
            parent_path = op.normpath(op.join(path, '..'))
            if parent_path == '.':
                parent_path = None

            items.append(('..', parent_path, True, 0))

        for f in os.listdir(directory):
            fp = op.join(directory, f)

            items.append((f, op.join(path, f), op.isdir(fp), op.getsize(fp)))

        # Sort by type
        items.sort(key=itemgetter(2), reverse=True)

        # Generate breadcrumbs
        accumulator = []
        breadcrumbs = []
        for n in path.split(os.sep):
            accumulator.append(n)
            breadcrumbs.append((n, op.join(*accumulator)))

        return self.render(self.list_template,
                           dir_path=path,
                           breadcrumbs=breadcrumbs,
                           get_dir_url=self._get_dir_url,
                           get_file_url=self._get_file_url,
                           items=items,
                           base_path=base_path)

    @expose('/upload/', methods=('GET', 'POST'))
    @expose('/upload/<path:path>', methods=('GET', 'POST'))
    def upload(self, path=None):
        """
            Upload view method

            `path`
                Optional directory path. If not provided,
                will use base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        if not self.can_upload:
            flash(gettext('File uploading is disabled.'), 'error')
            return redirect(self._get_dir_url('.index', path))

        form = UploadForm(self)
        if form.validate_on_submit():
            filename = op.join(directory,
                               secure_filename(form.upload.data.filename))

            if op.exists(filename):
                flash(gettext('File "%(name)s" already exists.',
                              name=form.upload.data.filename), 'error')
            else:
                try:
                    self.save_file(filename, form.upload.data)
                    return redirect(self._get_dir_url('.index', path))
                except Exception, ex:
                    flash(gettext('Failed to save file: %(error)s', error=ex))

        return self.render(self.upload_template,
                           form=form,
                           base_path=base_path,
                           path=path,
                           msg=gettext(u'Upload a file'))

    @expose('/mkdir/', methods=('GET', 'POST'))
    @expose('/mkdir/<path:path>', methods=('GET', 'POST'))
    def mkdir(self, path=None):
        """
            Directory creation view method

            `path`
                Optional directory path. If not provided,
                will use base directory
        """
        # Get path and verify if it is valid
        base_path, directory, path = self._normalize_path(path)

        dir_url = self._get_dir_url('.index', path)

        if not self.can_mkdir:
            flash(gettext('Directory creation is disabled.'), 'error')
            return redirect(dir_url)

        form = NameForm(request.form)

        if form.validate_on_submit():
            try:
                os.mkdir(op.join(directory, form.name.data))
                return redirect(dir_url)
            except Exception, ex:
                flash(gettext('Failed to create directory: %(error)s', ex),
                      'error')

        return self.render(self.mkdir_template,
                           form=form,
                           dir_url=dir_url,
                           base_path=base_path,
                           path=path,
                           msg=gettext(u'Create a new directory'))

    @expose('/delete/', methods=('POST',))
    def delete(self):
        """
            Delete view method
        """
        path = request.form.get('path')

        if not path:
            return redirect(url_for('.index'))

        # Get path and verify if it is valid
        base_path, full_path, path = self._normalize_path(path)

        return_url = self._get_dir_url('.index', op.dirname(path))

        if not self.can_delete:
            flash(gettext('Deletion is disabled.'))
            return redirect(return_url)

        if op.isdir(full_path):
            if not self.can_delete_dirs:
                flash(gettext('Directory deletion is disabled.'))
                return redirect(return_url)

            try:
                shutil.rmtree(full_path)
                flash(
                    gettext('Directory "%s" was successfully deleted.' % path)
                )
            except Exception, ex:
                flash(
                    gettext('Failed to delete directory: %(error)s', error=ex),
                    'error'
                )
        else:
            try:
                os.remove(full_path)
                flash(gettext('File "%(name)s" was successfully deleted.',
                              name=path))
            except Exception, ex:
                flash(gettext('Failed to delete file: %(name)s',
                              name=ex), 'error')

        return redirect(return_url)

    @expose('/rename/', methods=('GET', 'POST'))
    def rename(self):
        """
            Rename view method
        """
        path = request.args.get('path')

        if not path:
            return redirect(url_for('.index'))

        base_path, full_path, path = self._normalize_path(path)

        return_url = self._get_dir_url('.index', op.dirname(path))

        if not self.can_rename:
            flash(gettext('Renaming is disabled.'))
            return redirect(return_url)

        if not op.exists(full_path):
            flash(gettext('Path does not exist.'))
            return redirect(return_url)

        form = NameForm(request.form, name=op.basename(path))
        if form.validate_on_submit():
            try:
                dir_base = op.dirname(full_path)
                filename = secure_filename(form.name.data)

                os.rename(full_path, op.join(dir_base, filename))
                flash(gettext('Successfully renamed "%(src)s" to "%(dst)s"',
                      src=op.basename(path),
                      dst=filename))
            except Exception, ex:
                flash(gettext('Failed to rename: %(error)s',
                              error=ex), 'error')

            return redirect(return_url)

        return self.render(self.rename_template,
                           form=form,
                           path=op.dirname(path),
                           name=op.basename(path),
                           dir_url=return_url,
                           base_path=base_path)
