from datetime import date, datetime
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, MenuForm, MenuSectionForm, MenuItemForm



'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.context_processor
def inject_unread_count():
    if current_user.is_authenticated and current_user.id == 1:
        unread_count = db.session.execute(db.select(db.func.count(ContactMessage.id)).where(ContactMessage.is_read == False)).scalar()
        return dict(unread_count=unread_count)
    return dict(unread_count=0)


# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


class Base(DeclarativeBase):
    pass

# --- Database configuration ---
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///posts.db')
if db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
# For hosted Postgres providers (Railway/Supabase/Neon/etc.), SSL is commonly required.
# pool_pre_ping + pool_recycle help avoid stale connections after provider sleep/idle timeouts.
if db_uri.startswith('postgresql://'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'sslmode': os.environ.get('PGSSLMODE', 'require')},
        'pool_pre_ping': True,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '300')),
    }
db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)



class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
  
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    # Child Relationship to the BlogPosts
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")



class Menu(db.Model):
    __tablename__ = "menus"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(500), nullable=True)
    slug: Mapped[str] = mapped_column(String(250), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sections = relationship("MenuSection", back_populates="menu", cascade="all, delete-orphan")


class MenuSection(db.Model):
    __tablename__ = "menu_sections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    menu_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("menus.id"))
    menu = relationship("Menu", back_populates="sections")
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    items = relationship("MenuItem", back_populates="section", cascade="all, delete-orphan")


class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("menu_sections.id"))
    section = relationship("MenuSection", back_populates="items")
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[str] = mapped_column(String(50), nullable=True)
    img_url: Mapped[str] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(100), nullable=True)
    event_date: Mapped[str] = mapped_column(String(100), nullable=True)
    number_of_people: Mapped[str] = mapped_column(String(50), nullable=True)
    occasion: Mapped[str] = mapped_column(String(100), nullable=True)
    allergies: Mapped[str] = mapped_column(String(250), nullable=True)
    menus_interested: Mapped[str] = mapped_column(String(500), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    date_sent: Mapped[str] = mapped_column(String(100))


with app.app_context():
    db.create_all()


@app.route('/healthz')
def healthz():
    """Lightweight health check for platform probes (does not touch the database)."""
    return 'ok', 200

@app.route('/health')
def health_check():
    """Health check endpoint to verify app and database connection."""
    from flask import jsonify
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "app": "running",
        "database": "unknown"
    }
    
    try:
        # Test database connection
        db.session.execute(text("SELECT 1"))
        health_status["database"] = "connected"
        health_status["database_url"] = app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else "sqlite"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        health_status["error"] = str(e)
        return jsonify(health_status), 500
    
    return jsonify(health_status), 200

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if current_user.id != 1:
            return abort(403)
       
        return f(*args, **kwargs)

    return decorated_function



@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

       
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
          
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
   
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
            
    if form.errors:
        flash(f"Error en el formulario: {form.errors}")
    
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    try:
        result = db.session.execute(db.select(BlogPost))
        posts = result.scalars().all()
    except Exception as e:
        # If the DB is temporarily unavailable, don't crash the entire app.
        # Render/hosting health checks can hit this route.
        print('DB error on /:', e)
        posts = []
    seo_title = "Private Dining & Catering in The Hamptons | Serge Ristivojevic"
    seo_description = "Premier private dining and catering services in The Hamptons led by Executive Chef Serge Ristivojevic. Bespoke menus for intimate dinners and grand events."
    return render_template("index.html", all_posts=posts, current_user=current_user, seo_title=seo_title, seo_description=seo_description)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)



@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    
 
    all_menus = db.session.execute(db.select(Menu).where(Menu.is_active == True)).scalars().all()

    if request.method == "POST":
        data = request.form
        number_of_people = data["number_of_people"]
        event_date = data["event_date"]
        selected_menus = request.form.getlist("menus")
        menus_str = ", ".join(selected_menus) if selected_menus else "None"
        
     
        new_message = ContactMessage(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            event_date=event_date,
            number_of_people=number_of_people,
            occasion=data["ocassion"],
            allergies=data["allergies"],
            menus_interested=menus_str,
            message=data["message"],
            date_sent=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(new_message)
        db.session.commit()

        
        try:
            send_email(data["name"], data["email"], data["phone"], data["message"], number_of_people, event_date,data["ocassion"],data["allergies"], selected_menus)
        except Exception as e:
            print("RESEND FAILED:", e)
            flash("We received your message, but email delivery failed.")
        return render_template("contact.html", msg_sent=True, menus=all_menus, current_user=current_user)
    return render_template("contact.html", msg_sent=False, menus=all_menus, current_user=current_user)


def send_email(name, email, phone, message, number_of_people, event_date, occasion, allergies, menus_interested):
    api_key = os.environ.get("RESEND_API_KEY")
    to_email = os.environ.get("CONTACT_TO_EMAIL")
    from_email = os.environ.get("CONTACT_FROM_EMAIL", "onboarding@resend.dev")

    if not api_key or not to_email:
        raise RuntimeError("Missing RESEND_API_KEY or CONTACT_TO_EMAIL env vars")

    menus_str = ", ".join(menus_interested) if menus_interested else "None"

    html_content = render_template(
        "email_inquiry.html",
        name=name, email=email, phone=phone, message=message,
        number_of_people=number_of_people, event_date=event_date,
        occasion=occasion, allergies=allergies, menus=menus_str,
        year=datetime.now().year
    )

    text_content = (
        f"New inquiry from {name}\n\n"
        f"Email: {email}\nPhone: {phone}\n"
        f"Guests: {number_of_people}\nDate: {event_date}\n"
        f"Occasion: {occasion}\nAllergies: {allergies}\n"
        f"Menus: {menus_str}\n\nMessage:\n{message}"
    )

    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "from": from_email,
            "to": [to_email],
            "subject": f"New Inquiry: {name} - {event_date}",
            "reply_to": email,
            "text": text_content,
            "html": html_content,
            "cc": "sergeristivojevic@gmail.com"
        },
        timeout=10,
    )
    r.raise_for_status()


# -------------------- CONTACT MESSAGES ADMIN --------------------

@app.route("/admin/messages")
@admin_only
def admin_messages():
    messages = db.session.execute(db.select(ContactMessage).order_by(ContactMessage.id.desc())).scalars().all()
    menus = db.session.execute(db.select(Menu)).scalars().all()
    return render_template("admin_messages.html", messages=messages, menus=menus, current_user=current_user)

@app.route("/admin/message/<int:message_id>/delete")
@admin_only
def delete_message(message_id):
    msg = db.get_or_404(ContactMessage, message_id)
    db.session.delete(msg)
    db.session.commit()
    return redirect(url_for('admin_messages'))


@app.route("/admin/message/<int:message_id>/toggle_status")
@admin_only
def toggle_message_status(message_id):
    msg = db.get_or_404(ContactMessage, message_id)
    msg.is_read = not msg.is_read
    db.session.commit()
    return redirect(url_for('admin_messages'))

@app.route("/menus")
def menus():
  
    menus = db.session.execute(db.select(Menu).where(Menu.is_active == True)).scalars().all()
    seo_title = "Sample Menus & Culinary Offerings | Serge Ristivojevic"
    seo_description = "Explore our curated selection of private dining menus, from seasonal tasting experiences to family-style feasts. Fully customizable for your event."
    return render_template("menus.html", menus=menus, current_user=current_user, seo_title=seo_title, seo_description=seo_description)

@app.route("/services")
def services():
    return render_template("services.html", current_user=current_user)

from slugify import slugify

@app.route("/menu/<slug>")
def menu_detail(slug):
  
    menu = db.session.execute(db.select(Menu).where(Menu.slug == slug)).scalar()
    if not menu and slug.isdigit():
         menu = db.session.execute(db.select(Menu).where(Menu.id == int(slug))).scalar()
         
    if not menu:
        abort(404)

    if not menu.is_active and not (current_user.is_authenticated and current_user.id == 1):
        abort(404)
    
    all_menus = db.session.execute(db.select(Menu).where(Menu.is_active == True)).scalars().all()
    
    # SEO Logic
    seo_robots = "index, follow"
    seo_title = f"{menu.title} - Private Dining Menu | Serge Ristivojevic"
    if not menu.is_active:
        seo_robots = "noindex, nofollow"
        seo_title = f"[DRAFT] {menu.title} - Private Dining"
        
    seo_description = f"Explore our {menu.title}. {menu.subtitle if menu.subtitle else 'A curated private dining experience tailored to your tastes.'}"

    return render_template("menu_detail.html", menu=menu, all_menus=all_menus, current_user=current_user,
                           seo_title=seo_title, seo_description=seo_description, seo_robots=seo_robots)


@app.route("/admin/menus")
@admin_only
def admin_menus():
    menus = db.session.execute(db.select(Menu)).scalars().all()
    return render_template("admin_menus.html", menus=menus, current_user=current_user)

from werkzeug.utils import secure_filename
import secrets



app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_fn)
    form_picture.save(picture_path)
    return url_for('static', filename='uploads/' + picture_fn)



@app.route("/admin/menus/new", methods=["GET", "POST"])
@admin_only
def add_new_menu():
    form = MenuForm()
    if form.validate_on_submit():
        if form.img_file.data:
            picture_file = save_picture(form.img_file.data)
            menu_img_url = picture_file
        else:
            menu_img_url = None
            
  
        base_slug = slugify(form.title.data)
        slug = base_slug
        counter = 1
        while db.session.execute(db.select(Menu).where(Menu.slug == slug)).scalar_one_or_none():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        new_menu = Menu(
            title=form.title.data,
            subtitle=form.subtitle.data,
            img_url=menu_img_url,
            slug=slug,
            is_active=form.is_active.data
        )
        db.session.add(new_menu)
        db.session.commit()
        return redirect(url_for("admin_menus"))
    return render_template("edit_menu.html", form=form, is_edit=False, current_user=current_user, title="New Menu")

@app.route("/admin/menus/<int:menu_id>/edit", methods=["GET", "POST"])
@admin_only
def edit_menu(menu_id):
    menu = db.get_or_404(Menu, menu_id)
    form = MenuForm(
        title=menu.title,
        subtitle=menu.subtitle,
        is_active=menu.is_active
    )
    if form.validate_on_submit():
        menu.title = form.title.data
        menu.subtitle = form.subtitle.data
        current_slug = slugify(form.title.data) 
        if menu.slug != current_slug:

             existing = db.session.execute(db.select(Menu).where(Menu.slug == current_slug).where(Menu.id != menu_id)).scalar()
             if not existing:
                 menu.slug = current_slug
        
        if form.img_file.data:
            menu.img_url = save_picture(form.img_file.data)
        
        menu.is_active = form.is_active.data 
            
        db.session.commit()
        return redirect(url_for('admin_menus'))
    
  
    sections = db.session.execute(db.select(MenuSection).where(MenuSection.menu_id == menu_id).order_by(MenuSection.order)).scalars().all()
    
    return render_template("edit_menu.html", form=form, is_edit=True, menu=menu, sections=sections, current_user=current_user, title="Edit Menu")

@app.route("/admin/menus/<int:menu_id>/delete")
@admin_only
def delete_menu(menu_id):
    menu_to_delete = db.get_or_404(Menu, menu_id)
    db.session.delete(menu_to_delete)
    db.session.commit()
    return redirect(url_for('admin_menus'))

@app.route("/admin/menu/<int:menu_id>/toggle_status")
@admin_only
def toggle_menu_status(menu_id):
    menu = db.get_or_404(Menu, menu_id)
    menu.is_active = not menu.is_active
    db.session.commit()
    return redirect(url_for('admin_menus'))

# --- Section Routes ---

@app.route("/admin/menus/<int:menu_id>/section/new", methods=["GET", "POST"])
@admin_only
def add_menu_section(menu_id):
    menu = db.get_or_404(Menu, menu_id)
    # Auto-calculate next order number
    existing_sections = db.session.execute(db.select(MenuSection).where(MenuSection.menu_id == menu_id)).scalars().all()
    next_order = len(existing_sections) + 1
    
    form = MenuSectionForm()
    if request.method == 'GET':
        form.order.data = str(next_order)
        
    if form.validate_on_submit():
        new_section = MenuSection(
            title=form.title.data,
            subtitle=form.subtitle.data,
            order=int(form.order.data),
            menu=menu
        )
        db.session.add(new_section)
        db.session.commit()
        return redirect(url_for('edit_menu', menu_id=menu.id))
    return render_template("edit_section.html", form=form, menu=menu, current_user=current_user, title="Add Section")

@app.route("/admin/section/<int:section_id>/edit", methods=["GET", "POST"])
@admin_only
def edit_menu_section(section_id):
    section = db.get_or_404(MenuSection, section_id)
    form = MenuSectionForm(
        title=section.title,
        subtitle=section.subtitle,
        order=section.order
    )
    if form.validate_on_submit():
        section.title = form.title.data
        section.subtitle = form.subtitle.data
        section.order = int(form.order.data)
        db.session.commit()
        return redirect(url_for('edit_menu', menu_id=section.menu_id))
    return render_template("edit_section.html", form=form, menu=section.menu, current_user=current_user, title="Edit Section")

@app.route("/admin/section/<int:section_id>/delete")
@admin_only
def delete_menu_section(section_id):
    section = db.get_or_404(MenuSection, section_id)
    menu_id = section.menu_id
    db.session.delete(section)
    db.session.commit()
    return redirect(url_for('edit_menu', menu_id=menu_id))

# --- Item Routes ---

@app.route("/admin/section/<int:section_id>/item/new", methods=["GET", "POST"])
@admin_only
def add_menu_item(section_id):
    section = db.get_or_404(MenuSection, section_id)
    # Auto-calculate next order number
    existing_items = db.session.execute(db.select(MenuItem).where(MenuItem.section_id == section_id)).scalars().all()
    next_order = len(existing_items) + 1
    
    form = MenuItemForm()
    if request.method == 'GET':
        form.order.data = str(next_order)
        
    if form.validate_on_submit():
        img_url = None
        if form.img_file.data:
            img_url = save_picture(form.img_file.data)

        new_item = MenuItem(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            order=int(form.order.data),
            img_url=img_url,
            section=section
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('edit_menu', menu_id=section.menu_id))
    return render_template("edit_item.html", form=form, section=section, current_user=current_user, title="Add Item")

@app.route("/admin/item/<int:item_id>/edit", methods=["GET", "POST"])
@admin_only
def edit_menu_item(item_id):
    item = db.get_or_404(MenuItem, item_id)
    form = MenuItemForm(
        name=item.name,
        description=item.description,
        price=item.price,
        order=item.order
    )
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        item.price = form.price.data
        item.order = int(form.order.data)
        if form.img_file.data:
            item.img_url = save_picture(form.img_file.data)

        db.session.commit()
        return redirect(url_for('edit_menu', menu_id=item.section.menu_id))
    return render_template("edit_item.html", form=form, section=item.section, current_user=current_user, title="Edit Item")


@app.route("/admin/item/<int:item_id>/delete")
@admin_only
def delete_menu_item(item_id):
    item = db.get_or_404(MenuItem, item_id)
    menu_id = item.section.menu_id
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('edit_menu', menu_id=menu_id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", seo_title="Page Not Found | Serge Ristivojevic", seo_robots="noindex, nofollow"), 404


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(port=port)
