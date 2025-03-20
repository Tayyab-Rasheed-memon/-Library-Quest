import streamlit as st
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import logging
import random
import base64

# Configure logging
logging.basicConfig(filename='library_manager.log', level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
LIBRARY_FILE = "library.json"
USER_DATA_FILE = "user_data.json"
VALID_YEARS = range(1000, datetime.now().year + 1)
GENRE_OPTIONS = ["Fiction", "Non-Fiction", "Sci-Fi", "Fantasy", "Mystery", "Biography", "Romance", "Thriller", "Other"]
ACHIEVEMENTS = {
    "Novice Reader": {"books": 5, "icon": "🏆"},
    "Book Worm": {"books": 20, "icon": "🐛"},
    "Literary Master": {"books": 50, "icon": "📚"}
}

# Set page config as the first Streamlit command
st.set_page_config(page_title="Library Quest", page_icon="📚", layout="wide")

# Load and encode the local image as base64
def load_image_as_base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        st.error(f"Image file '{image_path}' not found. Using a placeholder image instead.")
        return "https://source.unsplash.com/random/200x200/?portrait"

class LibraryManager:
    def __init__(self):
        self.library: List[Dict] = self._load_library()
        self.recommendations = {
            "Fiction": ["To Kill a Mockingbird", "1984"],
            "Sci-Fi": ["Dune", "Foundation"],
            "Fantasy": ["Harry Potter", "Lord of the Rings"]
        }
        self.user_data = self._load_user_data()

    def _load_library(self) -> List[Dict]:
        try:
            with open(LIBRARY_FILE, "r", encoding='utf-8') as file:
                data = json.load(file)
                if not isinstance(data, list):
                    return []
                for book in data:
                    book.setdefault("notes", "")
                    book.setdefault("progress", 0)
                    book.setdefault("cover_image", None)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Error loading library: {str(e)}. Starting with empty library.")
            return []

    def _load_user_data(self) -> Dict:
        try:
            with open(USER_DATA_FILE, "r", encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "reading_streak": 0,
                "last_reading_date": None,
                "monthly_goal": 0,
                "books_read_this_month": 0,
                "month": datetime.now().month
            }

    def _save_library(self) -> None:
        try:
            with open(LIBRARY_FILE, "w", encoding='utf-8') as file:
                json.dump(self.library, file, indent=4)
            logging.info("Library successfully saved")
        except Exception as e:
            logging.error(f"Error saving library: {str(e)}")
            st.error("Failed to save library changes")

    def _save_user_data(self) -> None:
        try:
            with open(USER_DATA_FILE, "w", encoding='utf-8') as file:
                json.dump(self.user_data, file, indent=4)
        except Exception as e:
            logging.error(f"Error saving user data: {str(e)}")

    def add_book(self, title: str, author: str, year: int, genre: str, read: bool, 
                 rating: float = None, notes: str = "", cover_image: Optional[str] = None) -> bool:
        if not all([title.strip(), author.strip(), year in VALID_YEARS]):
            return False
        
        book = {
            "id": len(self.library) + 1,
            "title": title.strip(),
            "author": author.strip(),
            "year": year,
            "genre": genre,
            "read": read,
            "rating": rating,
            "notes": notes,
            "added_date": datetime.now().isoformat(),
            "progress": 0,
            "cover_image": cover_image
        }
        self.library.append(book)
        self._save_library()
        return True

    def remove_book(self, book_id: int) -> bool:
        initial_length = len(self.library)
        self.library = [book for book in self.library if book["id"] != book_id]
        if len(self.library) < initial_length:
            self._save_library()
            return True
        return False

    def update_progress(self, book_id: int, progress: int) -> bool:
        for book in self.library:
            if book["id"] == book_id:
                book["progress"] = min(100, max(0, progress))
                if progress == 100 and not book["read"]:
                    book["read"] = True
                    self._update_reading_streak()
                    self._update_monthly_goal()
                self._save_library()
                return True
        return False

    def _update_reading_streak(self):
        today = datetime.now().date()
        last_date = self.user_data["last_reading_date"]
        if last_date:
            last_date = datetime.fromisoformat(last_date).date()
            if today == last_date:
                return
            elif today == last_date + timedelta(days=1):
                self.user_data["reading_streak"] += 1
            else:
                self.user_data["reading_streak"] = 1
        else:
            self.user_data["reading_streak"] = 1
        self.user_data["last_reading_date"] = today.isoformat()
        self._save_user_data()

    def _update_monthly_goal(self):
        current_month = datetime.now().month
        if self.user_data["month"] != current_month:
            self.user_data["books_read_this_month"] = 0
            self.user_data["month"] = current_month
        self.user_data["books_read_this_month"] += 1
        self._save_user_data()

    def set_monthly_goal(self, goal: int):
        self.user_data["monthly_goal"] = max(0, goal)
        self._save_user_data()

    def get_achievements(self) -> List[str]:
        total_books = len(self.library)
        achieved = []
        for name, criteria in ACHIEVEMENTS.items():
            if total_books >= criteria["books"]:
                achieved.append(f"{criteria['icon']} {name}")
        return achieved

    def get_recommendation(self, genre: str) -> Optional[str]:
        return random.choice(self.recommendations.get(genre, [])) if genre in self.recommendations else None

def render_book_card(book: Dict):
    """Render a visually appealing book card with consistent styling"""
    status = "✅ Read" if book["read"] else f"📖 {book['progress']}%"
    rating = f"⭐ {book['rating']}/5" if book.get("rating") else ""
    notes = book.get("notes", "")
    cover_image = book.get("cover_image")
    
    # Only render the image if cover_image is a valid string (base64 or URL)
    if cover_image and isinstance(cover_image, str):
        try:
            st.image(cover_image, width=100)
        except Exception as e:
            logging.error(f"Error rendering cover image: {str(e)}")
            st.warning("Could not load cover image.")
    
    st.markdown(f"""
    <div class="card book-card">
        <h3 class="title">{book['title']}</h3>
        <p class="author">by {book['author']} ({book['year']})</p>
        <p class="genre">Genre: {book['genre']}</p>
        <p class="status">{status} {rating}</p>
        <p class="notes">{notes}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    if "manager" not in st.session_state:
        st.session_state.manager = LibraryManager()
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    manager = st.session_state.manager

    # Load the local profile picture
    profile_image = load_image_as_base64("github_dp_oval.png")

    # Custom CSS for profile card, book card, and animations
    st.markdown("""
    <style>
        /* Card styling for both profile and book cards */
        .card {
            background-color: #f5f5f5;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        /* Profile card specific styling */
        .profile-card {
            animation: bounceIn 1s ease-out;
        }

        .profile-pic {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            border: 3px solid #6a0dad; /* Purple border */
            object-fit: cover;
            margin: 0 auto;
            display: block;
        }

        .name {
            font-size: 18px;
            font-weight: bold;
            color: #000;
            margin: 10px 0 5px;
        }

        .username {
            font-size: 14px;
            color: #666;
            margin: 0;
        }

        .title {
            font-size: 16px;
            color: #1e90ff; /* Blue color */
            margin: 5px 0;
        }

        /* Book card specific styling */
        .book-card .title {
            font-size: 18px;
            font-weight: bold;
            color: #000;
            margin: 10px 0 5px;
        }

        .book-card .author {
            font-size: 14px;
            color: #666;
            margin: 0;
        }

        .book-card .genre {
            font-size: 16px;
            color: #1e90ff;
            margin: 5px 0;
        }

        .book-card .status {
            font-size: 14px;
            color: #28a745; /* Green for status */
            margin: 5px 0;
        }

        .book-card .notes {
            font-size: 14px;
            color: #666;
            margin: 5px 0;
        }

        /* Bounce-in animation for profile card */
        @keyframes bounceIn {
            0% {
                transform: scale(0.3);
                opacity: 0;
            }
            50% {
                transform: scale(1.05);
                opacity: 1;
            }
            70% {
                transform: scale(0.95);
            }
            100% {
                transform: scale(1);
            }
        }

        /* Hover effect for both cards */
        .card:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }

        /* Dark mode styling */
        .dark-mode .card {
            background-color: #333;
            color: #fff;
        }

        .dark-mode .name, .dark-mode .book-card .title {
            color: #fff;
        }

        .dark-mode .username, .dark-mode .book-card .author, .dark-mode .book-card .notes {
            color: #bbb;
        }
    </style>
    """, unsafe_allow_html=True)

    # Dark mode toggle
    if st.sidebar.checkbox("Dark Mode", value=st.session_state.dark_mode):
        st.session_state.dark_mode = True
        st.markdown('<style>body, .stApp {background-color: #1a1a1a; color: #ffffff;}</style>', unsafe_allow_html=True)
        st.markdown('<style>.dark-mode {background-color: #1a1a1a; color: #ffffff;}</style>', unsafe_allow_html=True)
    else:
        st.session_state.dark_mode = False

    # User Profile Card in Sidebar using github_dp_oval.png
    st.sidebar.markdown(f"""
    <div class="card profile-card">
        <img src="{profile_image}" class="profile-pic" alt="Profile Picture">
        <p class="name">Ibrahim Tayab</p>
        <p class="username">(Tayab.R)</p>
        <p class="title">📚 Library Manager</p>
    </div>
    """, unsafe_allow_html=True)

    st.title("📚 Library Quest")
    st.markdown("*Embark on your reading adventure!*")

    menu = st.sidebar.selectbox("Navigation", 
        ["Add Book", "My Library", "Reading Progress", "Remove Book", "Achievements", "Recommendations", "Goals", "Export"])

    if menu == "Add Book":
        st.header("📖 Add a New Adventure")
        with st.form("add_book_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Title *", max_chars=100)
                author = st.text_input("Author *", max_chars=100)
            with col2:
                year = st.number_input("Year *", min_value=min(VALID_YEARS), 
                                    max_value=max(VALID_YEARS), step=1)
                genre = st.selectbox("Genre", GENRE_OPTIONS)
            
            read = st.checkbox("Completed")
            rating = st.slider("Rating", 0.0, 5.0, step=0.1) if read else None
            notes = st.text_area("Notes", max_chars=500)
            cover_image = st.file_uploader("Upload Book Cover", type=["jpg", "png", "jpeg"])
            
            cover_image_data = None
            if cover_image:
                cover_image_data = base64.b64encode(cover_image.read()).decode("utf-8")
            
            if st.form_submit_button("Add to Quest"):
                if manager.add_book(title, author, year, genre, read, rating, notes, cover_image_data):
                    st.success(f"'{title}' joined your quest!")
                    st.balloons()

    elif menu == "My Library":
        st.header("📚 Your Collection")
        if manager.library:
            for book in manager.library:
                render_book_card(book)
        else:
            st.info("Your quest begins with adding books!")

    elif menu == "Reading Progress":
        st.header("📖 Reading Journey")
        if manager.library:
            book_options = {f"{book['title']} ({book['author']})": book["id"] for book in manager.library}
            selected_book = st.selectbox("Select a book", list(book_options.keys()))
            progress = st.slider("Reading Progress (%)", 0, 100, 
                               value=next((b["progress"] for b in manager.library if b["id"] == book_options[selected_book]), 0))
            if st.button("Update Progress"):
                if manager.update_progress(book_options[selected_book], progress):
                    st.success("Progress updated!")
                    share_link = f"https://libraryquest.com/share?book={selected_book}&progress={progress}"
                    st.markdown(f"Share your progress: [Click here]({share_link})")
                    st.rerun()
        else:
            st.info("Add books to track your progress!")

    elif menu == "Remove Book":
        st.header("🗑️ Remove a Book")
        if manager.library:
            book_options = {f"{book['title']} ({book['author']})": book["id"] for book in manager.library}
            selected_book = st.selectbox("Select a book to remove", list(book_options.keys()))
            if st.button("Remove Book"):
                if manager.remove_book(book_options[selected_book]):
                    st.success(f"'{selected_book}' has been removed from your library!")
                    st.rerun()
                else:
                    st.error("Failed to remove the book. Please try again.")
        else:
            st.info("No books available to remove.")

    elif menu == "Achievements":
        st.header("🏆 Your Achievements")
        achievements = manager.get_achievements()
        if achievements:
            for ach in achievements:
                st.markdown(f"*{ach}*")
            st.balloons()
            share_link = f"https://libraryquest.com/share?achievement={achievements[-1]}"
            st.markdown(f"Share your achievement: [Click here]({share_link})")
        else:
            st.info("Read more books to unlock achievements!")
        
        total_books = len(manager.library)
        next_goal = min([c["books"] for c in ACHIEVEMENTS.values() if c["books"] > total_books], default=0)
        if next_goal:
            st.progress(total_books / next_goal)
            st.write(f"Progress to next achievement: {total_books}/{next_goal} books")

        st.subheader("🔥 Reading Streak")
        st.write(f"Current streak: {manager.user_data['reading_streak']} days")

    elif menu == "Recommendations":
        st.header("🌟 Book Recommendations")
        genre = st.selectbox("Choose a genre", list(manager.recommendations.keys()))
        if st.button("Get Recommendation"):
            rec = manager.get_recommendation(genre)
            if rec:
                st.success(f"Try reading: **{rec}**")
                st.image("https://source.unsplash.com/300x200/?book", caption=rec)
            else:
                st.info("No recommendations available for this genre yet!")

    elif menu == "Goals":
        st.header("🎯 Reading Goals")
        goal = st.number_input("Set Monthly Reading Goal (books)", min_value=0, step=1)
        if st.button("Set Goal"):
            manager.set_monthly_goal(goal)
            st.success(f"Goal set to {goal} books per month!")
        
        books_read = manager.user_data["books_read_this_month"]
        monthly_goal = manager.user_data["monthly_goal"]
        if monthly_goal > 0:
            st.write(f"Progress: {books_read}/{monthly_goal} books read this month")
            st.progress(books_read / monthly_goal)
        else:
            st.info("Set a monthly goal to track your progress!")

    elif menu == "Export":
        if manager.library:
            df = pd.DataFrame(manager.library)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Your Quest Log",
                data=csv,
                file_name=f"library_quest_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            genre_counts = df["genre"].value_counts().to_dict()
            options = {
                "title": {"text": "Genre Distribution"},
                "tooltip": {},
                "series": [{"type": "pie", "data": [{"value": v, "name": k} for k, v in genre_counts.items()]}]
            }
            st_echarts(options=options, height="400px")
        else:
            st.info("Nothing to export yet!")

if __name__ == "__main__":
    main()