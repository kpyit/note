from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    
    id = db.Column(db.Integer, primary_key=True)#СТР 63 ТИПЫ 
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    
    #что то вроде записи ссылки на 2 таблицу   отношение один ко многим
    # backref Добавить обратную ссылку в другой модели в отношениях.
    # lazy Укажите, как должны загружаться связанные элементы.
    # Возможные значения:
    # select (элементы загружаются по по требованию при первом обращении к ним), 
    # immediate (элементы загружаются при загрузке исходного объекта),
    # joined (элементы загружаются немедленно, но как объединение), 
    # subquery (элементы загружаются немедленно, но как подзапрос),
    # noload (элементы никогда не загружаются), 
    # dynamic (вместо загрузки элементов, указывается запрос, который может их загрузить).
    posts = db.relationship('Post', backref='author', lazy='dynamic') #ссылка для другой базы backref,  dynamic не грузить просто запрос
    
    
    # Это не фактическое поле базы данных, а высокоуровневое представление о взаимоотношениях между users и posts, 
    # и по этой причине оно не находится в диаграмме базы данных. Для отношения «один ко многим» поле db.relationship 
    # обычно определяется на стороне «один» и используется как удобный способ получить доступ к «многим». 
    # Так, например, если у меня есть пользователь, хранящийся в u, выражение u.posts будет запускать запрос базы данных,
    # который возвращает все записи, написанные этим пользователем. 
    # Первый аргумент db.relationship указывает класс, который представляет сторону отношения «много».
    # Аргумент backref определяет имя поля, которое будет добавлено к объектам класса «много»,
    # который указывает на объект «один». Это добавит выражение post.author, которое вернет автора сообщения.
    # Аргумент lazy определяет, как будет выполняться запрос базы данных для связи, о чем я расскажу позже.
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    #сложная структура ясно что связь по полю id которое есть в обоих таблицах
    
    
    followed = db.relationship(
        
        'User',
        # secondary Укажите имя таблицы ассоциации для использования в отношениях "многие-ко-многим".
        secondary=followers,
        # primaryjoin Укажите условие соединения между двумя моделями в явном виде. Это необходимо только для неоднозначных отношений
        primaryjoin=(followers.c.follower_id == id),
        # secondaryjoin Укажите условие вторичного соединения для отношений "многие-ко-многим", когда SQLAlchemy не может определить его самостоятельно.
        secondaryjoin=(followers.c.followed_id == id),
        # backref Добавить обратную ссылку в другой модели в отношениях.
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')    
 

    def __repr__(self):
        return '<User {}>'.format(self.username)

    #для сохранения в базе хеша
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    # проверка хеша и охраненного пароля
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
 
 
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # db.ForeignKey('user.id') указатель на связанное поле с другой таблицей
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
