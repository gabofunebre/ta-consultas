import os
from functools import wraps
from flask import Flask, g, redirect, session, url_for, flash
from .config import Config
from .models import db, User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    @app.before_request
    def load_logged_in_user():
        user_id = session.get('user_id')
        g.user = User.query.get(user_id) if user_id else None

    @app.cli.command('init-db')
    def init_db_command():
        db.create_all()
        create_default_users()
        print('Base de datos inicializada con usuarios por defecto.')

    with app.app_context():
        db.create_all()
        create_default_users()

    return app


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash('Iniciá sesión para continuar.', 'warning')
            return redirect(url_for('main.login'))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.user is None:
                flash('Iniciá sesión para continuar.', 'warning')
                return redirect(url_for('main.login'))
            if g.user.role not in roles:
                flash('No tenés permisos para acceder a esta sección.', 'danger')
                return redirect(url_for('main.home'))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def create_default_users():
    defaults = [
        ('Administrador', 'admin@ta.local', 'admin123', 'admin'),
        ('Vendedor Demo', 'vendedor@ta.local', 'vendedor123', 'vendedor'),
    ]

    for nombre, email, pwd, role in defaults:
        if not User.query.filter_by(email=email).first():
            user = User(nombre=nombre, email=email, role=role)
            user.set_password(pwd)
            db.session.add(user)
    db.session.commit()
