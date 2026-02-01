# 🚀 GESA-2: Advanced Gamified Employability System

**GESA-2** (Gamified Employability Quotient Analyzer 2.0) is a significant evolution of the original employability assessment platform. It introduces a sophisticated **Level-Based Progression System**, **Adaptive Testing**, and a comprehensive **Admin Dashboard** to provide a dynamic and personalized career readiness journey for every user.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 🌟 What's New in V2?

### 1. 📈 Level-Based Progression
Unlike static quizzes, GESA-2 implements a true gamified learning curve.
*   **Unlockable Levels**: Users start at **Level 1** for each skill (Aptitude, Technical, Soft Skills) and must pass to unlock Level 2, 3, and beyond.
*   **Increasing Difficulty**: Each level presents harder questions, earning you more XP and higher status.

### 2. 🧠 Adaptive Testing
*   **Dynamic Difficulty**: The system includes an **Adaptive Assessment** mode where question difficulty adjusts in real-time based on your performance.
*   **Personalized Feedback**: Generates granular insights based on the difficulty of questions answered correctly.

### 3. 🛡️ Comprehensive Admin Module
A powerful backend for administrators to manage the entire ecosystem:
*   **Question Bank Management**: Add, edit, and delete questions directly from the UI.
*   **Level Control**: Configure pass percentages, rewards, and descriptions for each level.
*   **User Management**: Monitor user progress and leaderboard stats.

---

## ✨ Core Features

### 👤 For Students (Candidates)
*   **Interactive Dashboard**: Track your "Employability Quotient" (EQ) across multiple domains.
*   **Gamified Rewards**:
    *   **XP System**: Earn XP to rank up from *Beginner* → *Learning* → *Almost Ready* → *Job-Ready*.
    *   **Badges**: Unlock achievements for streaks, high scores, and activity.
    *   **Leaderboard**: Compete with peers for the top rank.
*   **Interview Simulator**: AI-powered mock interview module with instant feedback on response quality.
*   **Resume Analyzer**: Upload your CV for automated scoring and improvement tips.

### 👨‍💼 For Administrators
*   **Content Management System (CMS)**: full control over assessment content without touching code.
*   **Analytics**: View system-wide performance trends.

---

## 🛠️ Technical Stack

*   **Backend**: Python (Flask), SQLAlchemy (ORM)
*   **Database**: SQLite (Dev) / PostgreSQL (Prod)
*   **Frontend**: Jinja2 Templates, Bootstrap 5, Custom CSS
*   **Data Processing**: Pandas, Scikit-learn (for adaptive logic)

---

## 📂 Project Structure

```
GESA-2/
├── Gamified-Employability-Quotient-Analyzer-/  # Main Application Source
│   ├── app.py              # App entry point
│   ├── routes.py           # V2 Routes (Admin, Levels, Adaptive)
│   ├── models.py           # Enhanced DB Models (UserLevel, AssessmentLevel)
│   ├── utils.py            # Complex logic (Scoring, Recommendations)
│   └── templates/          # V2 Templates (Admin views, Adaptive quizzes)
├── pyproject.toml          # Dependency management
└── README.md
```

---

## 🚀 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/cyriac-pullan/GESA-2.git
    cd GESA-2/Gamified-Employability-Quotient-Analyzer-
    ```

2.  **Set up Virtual Environment**
    ```bash
    python -m venv venv
    
    # Windows
    venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize Database**
    The app automatically checks for an admin user on startup.
    *   **Default Admin Credentials**: (Check logs on first run or `create_admin` function)

5.  **Run the App**
    ```bash
    python app.py
    ```
    Access at: `http://127.0.0.1:5000`

---

## 🤝 Contributing

Contributions are welcome! Please fork the repo and submit a Pull Request.

---

## 👤 Author

**Cyriac Paul Pullan**
*   GitHub: [@cyriac-pullan](https://github.com/cyriac-pullan)
