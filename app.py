from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import uuid
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, render_template, redirect, url_for, flash


# Config
app = Flask(__name__)
app.secret_key = "supersecretkey"  # later move to config.py

DATABASE = os.path.join("db", "social.db")

# Upload config
UPLOAD_FOLDER = os.path.join("static", "uploads")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Load user from DB
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1], row[2])
    return None

# --------------------
# Routes
# --------------------

@app.route("/")
def index():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT posts.id, posts.content, posts.image, posts.timestamp, users.username
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.timestamp DESC
    """)
    posts = cursor.fetchall()
    conn.close()

    return render_template("index.html", user=current_user, posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = generate_password_hash(password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists", "danger")
        conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and check_password_hash(row[2], password):
            user = User(row[0], row[1], row[2])
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        content = request.form["content"]
        file = request.files.get("image")
        filename = None

        if file and file.filename != "":
            # make filename unique
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (user_id, content, image) VALUES (?, ?, ?)",
                       (current_user.id, content, filename))
        conn.commit()
        conn.close()

        flash("Post created successfully!", "success")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("create_post.html")


@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id=? AND user_id=?", (post_id, current_user.id))
    post = cursor.fetchone()

    if not post:
        flash("Post not found or not yours!", "danger")
        conn.close()
        return redirect(url_for("index"))

    if request.method == "POST":
        new_content = request.form["content"]
        cursor.execute("UPDATE posts SET content=? WHERE id=?", (new_content, post_id))
        conn.commit()
        conn.close()
        flash("Post updated successfully!", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit_post.html", post=post)


@app.route("/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id=? AND user_id=?", (post_id, current_user.id))
    conn.commit()
    conn.close()
    flash("Post deleted successfully!", "info")
    return redirect(url_for("index"))


@app.route("/profile/<string:username>")
def profile(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get user details
    cursor.execute("SELECT id, username, bio, profile_pic FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        flash("User not found!", "danger")
        return redirect(url_for("index"))

    user_id = user[0]

    # Get that user’s posts
    cursor.execute("""
        SELECT id, content, image, timestamp
        FROM posts
        WHERE user_id=?
        ORDER BY timestamp DESC
    """, (user_id,))
    posts = cursor.fetchall()

    # Check if current_user is following this profile
    is_following = False
    if current_user.is_authenticated and current_user.id != user_id:
        cursor.execute("SELECT * FROM follows WHERE follower_id=? AND following_id=?",
                       (current_user.id, user_id))
        if cursor.fetchone():
            is_following = True

    # Get followers count
    cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id=?", (user_id,))
    followers_count = cursor.fetchone()[0]

    # Get following count
    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id=?", (user_id,))
    following_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        profile_user=user,
        posts=posts,
        is_following=is_following,
        followers_count=followers_count,
        following_count=following_count
    )


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch current user details from DB
    cursor.execute("SELECT username, bio, profile_pic FROM users WHERE id = ?", (current_user.id,))
    user_data = cursor.fetchone()

    if request.method == 'POST':
        new_username = request.form.get('username')
        new_bio = request.form.get('bio')

        # Handle profile picture
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            cursor.execute("UPDATE users SET profile_pic = ? WHERE id = ?",
                           (filename, current_user.id))
            conn.commit()

        # ✅ Update username if not taken
        if new_username and new_username != current_user.username:
            cursor.execute("SELECT id FROM users WHERE username = ?", (new_username,))
            existing_user = cursor.fetchone()
            if existing_user:
                conn.close()
                flash('❌ Username already taken, please choose another.', 'danger')
                return redirect(url_for('edit_profile'))

            cursor.execute("UPDATE users SET username = ? WHERE id = ?",
                           (new_username, current_user.id))
            conn.commit()

        # ✅ Update bio
        if new_bio is not None:
            cursor.execute("UPDATE users SET bio = ? WHERE id = ?",
                           (new_bio, current_user.id))
            conn.commit()

        conn.close()
        flash('✅ Profile updated successfully!', 'success')
        return redirect(url_for('profile', username=new_username or current_user.username))

    conn.close()
    return render_template('edit_profile.html', user_data=user_data)



@app.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id):
    if user_id == current_user.id:
        flash("You cannot follow yourself!", "warning")
        return redirect(url_for("profile", username=current_user.username))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM follows WHERE follower_id=? AND following_id=?",
                   (current_user.id, user_id))
    if cursor.fetchone():
        flash("Already following this user", "info")
    else:
        cursor.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)",
                       (current_user.id, user_id))
        conn.commit()
        flash("User followed successfully!", "success")
    conn.close()
    # Redirect back to the profile page of the followed user
    cursor = sqlite3.connect(DATABASE).cursor()
    cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
    username_row = cursor.fetchone()
    return redirect(url_for("profile", username=username_row[0]))


@app.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM follows WHERE follower_id=? AND following_id=?",
                   (current_user.id, user_id))
    conn.commit()
    conn.close()
    flash("User unfollowed successfully!", "info")

    cursor = sqlite3.connect(DATABASE).cursor()
    cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
    username_row = cursor.fetchone()
    return redirect(url_for("profile", username=username_row[0]))


@app.route("/users")
@login_required
def users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id != ?", (current_user.id,))
    all_users = cursor.fetchall()
    conn.close()
    return render_template("users.html", users=all_users)



@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password")
        new_pw = request.form.get("new_password")
        confirm_pw = request.form.get("confirm_password")

        # Check if current password is correct
        if not check_password_hash(current_user.password_hash, current_pw):
            flash("❌ Current password is incorrect", "danger")
            return redirect(url_for("change_password"))

        # Check if new password and confirm password match
        if new_pw != confirm_pw:
            flash("❌ New password and confirm password do not match", "danger")
            return redirect(url_for("change_password"))

        # Hash the new password and update in DB
        new_hashed_pw = generate_password_hash(new_pw)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                       (new_hashed_pw, current_user.id))
        conn.commit()
        conn.close()

        flash("✅ Password changed successfully!", "success")
        return redirect(url_for("profile", username=current_user.username))

    # GET request: render the change password form
    return render_template("change_password.html")

if __name__ == "__main__":
    app.run(debug=True)
