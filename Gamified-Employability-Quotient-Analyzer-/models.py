from app import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100))
    cgpa = db.Column(db.Float, default=0.0)
    year_of_study = db.Column(db.String(20))
    major = db.Column(db.String(100))
    
    # Gamification fields
    total_xp = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20), default='Beginner')
    total_points = db.Column(db.Integer, default=0)
    employability_score = db.Column(db.Float, default=0.0)
    
    # Profile settings
    show_on_leaderboard = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')
    badges = db.relationship('UserBadge', backref='user', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='user', lazy=True, cascade='all, delete-orphan')
    challenges = db.relationship('UserChallenge', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def add_xp(self, xp_points):
        self.total_xp += xp_points
        self.update_level()
        db.session.commit()
    
    def update_level(self):
        if self.total_xp < 100:
            self.level = 'Beginner'
        elif self.total_xp < 500:
            self.level = 'Learning'
        elif self.total_xp < 1000:
            self.level = 'Almost Ready'
        else:
            self.level = 'Job-Ready'
    
    def get_level_progress(self):
        level_thresholds = {
            'Beginner': 100,
            'Learning': 500,
            'Almost Ready': 1000,
            'Job-Ready': float('inf')
        }
        
        current_threshold = level_thresholds.get(self.level, 100)
        if current_threshold == float('inf'):
            return 100
        
        if self.level == 'Beginner':
            return int((self.total_xp / current_threshold) * 100)
        elif self.level == 'Learning':
            return int(((self.total_xp - 100) / (current_threshold - 100)) * 100)
        elif self.level == 'Almost Ready':
            return int(((self.total_xp - 500) / (current_threshold - 500)) * 100)
        
        return 100

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)  # aptitude, technical, soft_skills
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    questions_data = db.Column(db.Text)  # JSON string of questions and answers
    time_taken = db.Column(db.Integer)  # in seconds
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_percentage(self):
        return round((self.score / self.max_score) * 100, 1)

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='fas fa-award')
    color = db.Column(db.String(20), default='gold')
    criteria = db.Column(db.Text)  # JSON string describing criteria
    xp_reward = db.Column(db.Integer, default=50)

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    badge = db.relationship('Badge', backref='user_badges')

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points_earned = db.Column(db.Integer, default=0)
    xp_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    analysis_data = db.Column(db.Text)  # JSON string of analysis results
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='resumes')

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    challenge_type = db.Column(db.String(20), nullable=False)  # daily, weekly
    target_value = db.Column(db.Integer, default=1)
    xp_reward = db.Column(db.Integer, default=25)
    points_reward = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    challenge = db.relationship('Challenge', backref='user_challenges')

class MockInterview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions_data = db.Column(db.Text)  # JSON string of questions and responses
    overall_score = db.Column(db.Float, default=0.0)
    feedback = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='mock_interviews')


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)  # aptitude, technical, soft_skills, adaptive
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5 for adaptive, 1 for others
    category = db.Column(db.String(100))  # math, programming, leadership, etc.
    options = db.Column(db.Text, nullable=False)  # JSON string of options
    correct_answer = db.Column(db.String(500), nullable=False)
    explanation = db.Column(db.Text)  # Optional explanation
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_options_list(self):
        """Return options as a Python list"""
        return json.loads(self.options)
    
    def set_options_list(self, options_list):
        """Set options from a Python list"""
        self.options = json.dumps(options_list)
    
    @staticmethod
    def get_questions_by_type(assessment_type, difficulty=None):
        """Get questions by assessment type and optional difficulty"""
        query = Question.query.filter_by(assessment_type=assessment_type, is_active=True)
        if difficulty:
            query = query.filter_by(difficulty_level=difficulty)
        return query.all()
    
    def to_dict(self):
        """Convert question to dictionary format"""
        return {
            'id': self.id,
            'question': self.question_text,
            'options': self.get_options_list(),
            'correct': self.correct_answer,
            'difficulty': self.difficulty_level,
            'category': self.category
        }


class UserLevel(db.Model):
    """Track user progress through different levels for each assessment type"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)  # aptitude, technical, soft_skills
    current_level = db.Column(db.Integer, default=1)
    unlocked_levels = db.Column(db.String(100), default='1')  # comma-separated list of unlocked levels
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='user_levels')
    
    def get_unlocked_levels_list(self):
        """Return list of unlocked levels as integers"""
        if not self.unlocked_levels:
            return [1]
        return [int(level) for level in self.unlocked_levels.split(',')]
    
    def unlock_level(self, level):
        """Unlock a specific level"""
        unlocked = self.get_unlocked_levels_list()
        if level not in unlocked:
            unlocked.append(level)
            unlocked.sort()
            self.unlocked_levels = ','.join(map(str, unlocked))
            self.current_level = max(self.current_level, level)
            db.session.commit()
    
    def is_level_unlocked(self, level):
        """Check if a specific level is unlocked"""
        return level in self.get_unlocked_levels_list()
    
    @staticmethod
    def get_or_create_user_level(user_id, assessment_type):
        """Get or create UserLevel for a user and assessment type"""
        user_level = UserLevel.query.filter_by(user_id=user_id, assessment_type=assessment_type).first()
        if not user_level:
            user_level = UserLevel(user_id=user_id, assessment_type=assessment_type)
            db.session.add(user_level)
            db.session.commit()
        return user_level


class AssessmentLevel(db.Model):
    """Define different levels for each assessment type"""
    id = db.Column(db.Integer, primary_key=True)
    assessment_type = db.Column(db.String(50), nullable=False)  # aptitude, technical, soft_skills
    level_number = db.Column(db.Integer, nullable=False)
    level_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    pass_percentage = db.Column(db.Float, default=70.0)  # percentage needed to pass
    xp_reward = db.Column(db.Integer, default=100)
    points_reward = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AssessmentLevel {self.assessment_type} Level {self.level_number}>'
