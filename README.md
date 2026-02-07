MySocial is a small social media web application built using **Flask**, **SQLite**, and **HTML/CSS**. It allows users to register, log in, create posts with optional images, follow other users, and manage their profiles. The project demonstrates full-stack web development concepts including authentication, database management, CRUD operations, and front-end design.

---

#Features

1. **User Registration & Authentication**
   Users can sign up with a unique username and password. Passwords are securely hashed. Login functionality allows access to features such as posting and following.

2. **Profile Management**
   Each user has a profile page displaying username, bio, profile picture, followers, and following counts. Users can edit their username, bio, and profile picture. Profiles show the user's posts with edit/delete options for their own content.

3. **Posts**
   Users can create text posts and optionally upload images. Posts are timestamped and displayed in a Pinterest-style grid on the main feed and profile pages. Posts include the author’s username (clickable to their profile).

4. **Follow/Unfollow System**
   Users can follow or unfollow others. Followers and following counts are displayed on each profile. This enables social interaction between users.

5. **Feed**
   The main feed shows posts from all users in reverse chronological order. Each post is displayed as a card with the author, timestamp, content, and image (if any).

6. **Password Management**
   Users can securely change their password from a settings dropdown in the navbar, which also provides a logout option.

---

#File Structure

- `app.py`: Main Flask backend with routes for authentication, posts, profiles, and follows.
- `templates/`: HTML templates (`index.html`, `profile.html`, `edit_profile.html`, `create_post.html`, etc.) extending `base.html`.
- `static/css/style.css`: Contains all styling for navbar, posts, buttons, forms, and responsive layouts.
- `static/uploads/`: Stores uploaded profile pictures and post images.
- `db/social.db`: SQLite database storing users, posts, and follow relationships.

---

#Design Choices

**Flask + SQLite**: Lightweight, portable, and sufficient for a small social media app.
**Responsive Design**: Posts display in a grid layout to mimic Pinterest-style blocks.
**Security**: Passwords are hashed; profile and post editing restricted to owners.
**User Experience**: Clean light-purple theme, navbar with Home, My Profile, and settings dropdown.

---

MySocial showcases a functional social media prototype, combining front-end styling and back-end logic to create an interactive user experience.
