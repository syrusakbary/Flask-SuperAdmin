from flask import Flask, url_for, redirect, render_template, request
try:
    from mongoengine import *
except ImportError:
    exit('You must have mongoengine installed. Install it with the command:\n\t$> easy_install mongoengine')

from flask.ext import superadmin, login, wtf
from flask.ext.superadmin.contrib import mongoenginemodel
from wtforms.fields import TextField, PasswordField
from wtforms.validators import Required, ValidationError

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Database name for Mongo
app.config['DATABASE'] = 'dummy_db'


# Create user model. For simplicity, it will store passwords in plain text.
# Obviously that's not right thing to do in real world application.
class User(Document):
    id = StringField(primary_key=True)
    login = StringField(max_length=80, unique=True)
    email = EmailField(max_length=120)
    password = StringField(max_length=64)

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.login


# Define login and registration forms (for flask-login)
class LoginForm(wtf.Form):
    login = TextField(validators=[Required()])
    password = PasswordField(validators=[Required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise ValidationError('Invalid user')

        if user.password != self.password.data:
            raise ValidationError('Invalid password')

    def get_user(self):
        return User.objects.get(login=self.login)


class RegistrationForm(wtf.Form):
    login = TextField(validators=[Required()])
    email = TextField()
    password = PasswordField(validators=[Required()])

    def validate_login(self, field):
        if len(User.objects(login=self.login.data)) > 0:
            raise ValidationError('Duplicate username')


# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.setup_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects.get(id=user_id)


# Create customized model view class
class MyModelView(mongoenginemodel.ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated()


# Create customized index view class
class MyAdminIndexView(superadmin.AdminIndexView):
    def is_accessible(self):
        return login.current_user.is_authenticated()


# Flask views
@app.route('/')
def index():
    return render_template('index.html', user=login.current_user)


@app.route('/login/', methods=('GET', 'POST'))
def login_view():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = form.get_user()
        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('form.html', form=form)


@app.route('/register/', methods=('GET', 'POST'))
def register_view():
    form = RegistrationForm(request.form)
    if form.validate_on_submit():
        user = User()

        form.populate_obj(user)
        user.id = user.login
        user.save()
        login.login_user(user)

        return redirect(url_for('index'))

    return render_template('form.html', form=form)


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Initialize flask-login
    init_login()

    # Mongoengine connection
    connect(app.config['DATABASE'])

    # Create admin
    admin = superadmin.Admin(app, 'Auth', index_view=MyAdminIndexView())

    # Add view
    admin.add_view(MyModelView(User))

    # Start app
    app.debug = True
    app.run()

