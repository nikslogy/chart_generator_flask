from flask import Flask
from chartgenerator.config.config import Config
from chartgenerator.routes.file_routes import file_bp
from chartgenerator.routes.chart_routes import chart_bp
import os

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Register blueprints
    app.register_blueprint(file_bp)
    app.register_blueprint(chart_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 