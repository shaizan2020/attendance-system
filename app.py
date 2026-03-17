import os
from flask import Flask, redirect, url_for, session
from flask_session import Session
from dotenv import load_dotenv

load_dotenv()

from config import Config
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.faculty import faculty_bp
from routes.student import student_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Flask-Session
    Session(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(student_bp)

    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role')
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            elif role == 'student':
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    @app.template_filter('strftime')
    def strftime_filter(value, fmt='%b %d, %Y %H:%M'):
        """Format a datetime object in Jinja2 templates."""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime(fmt)
        return str(value)

    @app.template_filter('objectid_str')
    def objectid_str_filter(value):
        return str(value) if value else ''

    # Make Python builtins available in templates
    app.jinja_env.globals.update(enumerate=enumerate, min=min, max=max, len=len)

    @app.context_processor
    def inject_user():
        return {
            'current_user_name': session.get('name', ''),
            'current_user_role': session.get('role', ''),
            'current_user_id': session.get('user_id', ''),
        }

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('500.html'), 500

    return app

# Create app at module level so gunicorn can find it (gunicorn app:app)
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
