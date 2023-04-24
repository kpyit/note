from app import create_app, db, cli
from app.models import User, Post

app = create_app()
#app = create_app(os.getenv('FLASK_CONFIG') or 'default') с выбором конфига
cli.register(app)

#контекст для shell оболоки запущенного сервера
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}
 
