from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email


@bp.route('/login', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm() #forms.py  вот тут задается класс для работы обрработки полей валидатормаи
    if form.validate_on_submit(): #валидация полей формы автоподтягивается внутренней механикой для всех полей класса form
        
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            #до упрощения формы оно выводилось отдельным кодом через get_flashed_messages() в форме отрабатывают 1 раз
            flash(_('Invalid username or password'))#обратная связь сообщение пользователю что вход неудачный
            return redirect(url_for('auth.login'))

        #Регистрация пользователя через модуль flask_login
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')#по идее тут имя функции view 
            
        return redirect(next_page)#просто редирект на расчитанный url 
    
    #форма сечас формируется по быстрому расширением flask_wtf в шаблоне
    #с помощью готовых шалонов bootstrap 'bootstrap/wtf.html' as wtf СТР47
    return render_template('auth/login.html', title=_('Sign In'), form=form)






@bp.route('/logout')
def logout():
    # разлогиниваем пользователя через модуль flask_login
    logout_user()
    return redirect(url_for('main.index'))



@bp.route('/register', methods=['GET', 'POST'])
def register():
    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()#интересный механизм дефолтная форма для регистрации в модулях
    if form.validate_on_submit():#валидация полей 
        
        user = User(username=form.username.data, email=form.email.data)
        
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title=_('Register'),
                           form=form)



@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.verify_reset_password_token(token)
    
    if not user:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)
