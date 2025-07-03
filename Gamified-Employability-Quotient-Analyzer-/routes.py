from flask import render_template, request, redirect, url_for, session, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Assessment, Badge, UserBadge, Activity, Resume, Challenge, UserChallenge, MockInterview, Question, UserLevel, AssessmentLevel
from utils import calculate_employability_score, analyze_resume, create_default_badges, create_default_challenges, get_assessment_questions, grade_assessment, award_badges, get_mock_interview_questions, get_next_adaptive_question, grade_adaptive_assessment
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        cgpa = float(request.form.get('cgpa', 0.0))
        year_of_study = request.form['year_of_study']
        major = request.form['major']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            cgpa=cgpa,
            year_of_study=year_of_study,
            major=major
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create welcome activity
        activity = Activity(
            user_id=user.id,
            activity_type='registration',
            description='Welcome to Employability Game!',
            points_earned=50,
            xp_earned=25
        )
        db.session.add(activity)
        
        user.total_points += 50
        user.add_xp(25)
        
        flash('Registration successful! Welcome to the game!', 'success')
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
    
    # Get recent activities
    recent_activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.created_at.desc()).limit(5).all()
    
    # Get user badges
    user_badges = UserBadge.query.filter_by(user_id=user.id).join(Badge).all()
    
    # Get active challenges
    active_challenges = UserChallenge.query.filter_by(
        user_id=user.id, 
        completed=False
    ).join(Challenge).limit(3).all()
    
    # Calculate employability score
    user.employability_score = calculate_employability_score(user)
    db.session.commit()
    
    return render_template('dashboard.html', 
                         user=user, 
                         activities=recent_activities,
                         badges=user_badges,
                         challenges=active_challenges)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
    
    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.cgpa = float(request.form.get('cgpa', user.cgpa))
        user.year_of_study = request.form['year_of_study']
        user.major = request.form['major']
        user.show_on_leaderboard = 'show_on_leaderboard' in request.form
        
        db.session.commit()
        
        # Award points for profile update
        activity = Activity(
            user_id=user.id,
            activity_type='profile_update',
            description='Updated profile information',
            points_earned=10,
            xp_earned=5
        )
        db.session.add(activity)
        user.total_points += 10
        user.add_xp(5)
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/assessments')
def assessments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user_assessments = Assessment.query.filter_by(user_id=user.id).order_by(Assessment.completed_at.desc()).all()
    
    # Group assessments by type
    assessment_summary = {}
    for assessment in user_assessments:
        if assessment.assessment_type not in assessment_summary:
            assessment_summary[assessment.assessment_type] = []
        assessment_summary[assessment.assessment_type].append(assessment)
    
    # Get user levels for each assessment type
    user_levels = {}
    for assessment_type in ['aptitude', 'technical', 'soft_skills']:
        user_level = UserLevel.get_or_create_user_level(user.id, assessment_type)
        user_levels[assessment_type] = user_level
    
    # Get available levels for each assessment type
    available_levels = {}
    for assessment_type in ['aptitude', 'technical', 'soft_skills']:
        available_levels[assessment_type] = AssessmentLevel.query.filter_by(
            assessment_type=assessment_type, 
            is_active=True
        ).order_by(AssessmentLevel.level_number).all()
    
    return render_template('assessments.html', 
                         user=user, 
                         assessment_summary=assessment_summary,
                         user_levels=user_levels,
                         available_levels=available_levels)

@app.route('/assessment/<assessment_type>')
@app.route('/assessment/<assessment_type>/<int:level>')
def take_assessment(assessment_type, level=1):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if assessment_type not in ['aptitude', 'technical', 'soft_skills', 'adaptive']:
        flash('Invalid assessment type', 'error')
        return redirect(url_for('assessments'))
    
    user = User.query.get(session['user_id'])
    
    # For leveled assessments, check if level is unlocked
    if assessment_type in ['aptitude', 'technical', 'soft_skills']:
        user_level = UserLevel.get_or_create_user_level(user.id, assessment_type)
        if not user_level.is_level_unlocked(level):
            flash(f'Level {level} is not unlocked yet. Complete previous levels first.', 'error')
            return redirect(url_for('assessments'))
        
        # Store current level in session
        session['current_level'] = level
        session['assessment_level_info'] = AssessmentLevel.query.filter_by(
            assessment_type=assessment_type,
            level_number=level
        ).first().id if AssessmentLevel.query.filter_by(
            assessment_type=assessment_type,
            level_number=level
        ).first() else None
    
    if assessment_type == 'adaptive':
        # Initialize adaptive assessment session
        session['adaptive_data'] = {
            'current_difficulty': 2,
            'correct_streak': 0,
            'total_answered': 0,
            'questions_data': [],
            'current_question': None
        }
        
        # Get first question
        question, difficulty = get_next_adaptive_question(2, 0, 0)
        session['adaptive_data']['current_question'] = question
        session['adaptive_data']['current_difficulty'] = difficulty
        
        return render_template('adaptive_assessment.html', 
                             assessment_type=assessment_type,
                             question=question,
                             difficulty=difficulty)
    else:
        questions = get_assessment_questions(assessment_type)
        return render_template('assessment_quiz.html', 
                             assessment_type=assessment_type,
                             questions=questions)

@app.route('/submit_adaptive_answer', methods=['POST'])
def submit_adaptive_answer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'adaptive_data' not in session:
        return redirect(url_for('assessments'))
    
    adaptive_data = session['adaptive_data']
    current_question = adaptive_data['current_question']
    answer = request.form['answer']
    
    # Check if answer is correct
    is_correct = answer == current_question['correct']
    
    # Update question data
    question_data = {
        'question': current_question['question'],
        'difficulty': current_question['difficulty'],
        'is_correct': is_correct,
        'answer': answer,
        'correct_answer': current_question['correct']
    }
    
    adaptive_data['questions_data'].append(question_data)
    adaptive_data['total_answered'] += 1
    
    # Update streak
    if is_correct:
        adaptive_data['correct_streak'] += 1
    else:
        adaptive_data['correct_streak'] = 0
    
    # Check if assessment should end (after 10 questions or based on confidence)
    if adaptive_data['total_answered'] >= 10:
        return redirect(url_for('finish_adaptive_assessment'))
    
    # Get next question
    next_question, new_difficulty = get_next_adaptive_question(
        adaptive_data['current_difficulty'],
        adaptive_data['correct_streak'],
        adaptive_data['total_answered']
    )
    
    adaptive_data['current_question'] = next_question
    adaptive_data['current_difficulty'] = new_difficulty
    session['adaptive_data'] = adaptive_data
    
    return render_template('adaptive_assessment.html',
                         assessment_type='adaptive',
                         question=next_question,
                         difficulty=new_difficulty,
                         question_number=adaptive_data['total_answered'] + 1,
                         is_correct=is_correct)

@app.route('/finish_adaptive_assessment')
def finish_adaptive_assessment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'adaptive_data' not in session:
        return redirect(url_for('assessments'))
    
    user = User.query.get(session['user_id'])
    adaptive_data = session['adaptive_data']
    
    # Grade the adaptive assessment
    results = grade_adaptive_assessment(adaptive_data['questions_data'])
    
    # Save assessment
    assessment = Assessment(
        user_id=user.id,
        assessment_type='adaptive',
        score=results['total_score'],
        max_score=results['max_possible'],
        questions_data=json.dumps(adaptive_data['questions_data'])
    )
    db.session.add(assessment)
    
    # Award points and XP based on adaptive results
    percentage = results['percentage']
    base_points = 75  # Higher base for adaptive
    base_xp = 50     # Higher base for adaptive
    
    if percentage >= 90:
        points = base_points + 50
        xp = base_xp + 30
    elif percentage >= 80:
        points = base_points + 35
        xp = base_xp + 25
    elif percentage >= 70:
        points = base_points + 20
        xp = base_xp + 15
    else:
        points = base_points
        xp = base_xp
    
    activity = Activity(
        user_id=user.id,
        activity_type='adaptive_assessment',
        description=f'Completed Adaptive Assessment - {results["skill_level"]} level ({percentage:.1f}%)',
        points_earned=points,
        xp_earned=xp
    )
    db.session.add(activity)
    
    user.total_points += points
    user.add_xp(xp)
    
    # Update employability score
    user.employability_score = calculate_employability_score(user)
    
    # Award badges
    award_badges(user, 'adaptive', percentage)
    
    db.session.commit()
    
    # Clear adaptive session data
    session.pop('adaptive_data', None)
    
    flash(f'Adaptive assessment completed! Skill level: {results["skill_level"]}', 'success')
    return render_template('adaptive_results.html', 
                         results=results, 
                         points=points, 
                         xp=xp)

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    assessment_type = request.form['assessment_type']
    answers = {}
    
    # Collect answers
    for key, value in request.form.items():
        if key.startswith('question_'):
            question_id = key.replace('question_', '')
            answers[question_id] = value
    
    # Grade the assessment
    score, max_score, feedback = grade_assessment(assessment_type, answers)
    
    # Save assessment
    assessment = Assessment(
        user_id=user.id,
        assessment_type=assessment_type,
        score=score,
        max_score=max_score,
        questions_data=json.dumps(answers)
    )
    db.session.add(assessment)
    
    # Award points and XP
    percentage = (score / max_score) * 100
    base_points = 50
    base_xp = 30
    
    if percentage >= 90:
        points = base_points + 30
        xp = base_xp + 20
    elif percentage >= 80:
        points = base_points + 20
        xp = base_xp + 15
    elif percentage >= 70:
        points = base_points + 10
        xp = base_xp + 10
    else:
        points = base_points
        xp = base_xp
    
    activity = Activity(
        user_id=user.id,
        activity_type='assessment',
        description=f'Completed {assessment_type.replace("_", " ").title()} Assessment ({percentage:.1f}%)',
        points_earned=points,
        xp_earned=xp
    )
    db.session.add(activity)
    
    user.total_points += points
    user.add_xp(xp)
    
    # Check for badges
    award_badges(user, assessment_type, percentage)
    
    db.session.commit()
    
    flash(f'Assessment completed! Score: {percentage:.1f}% (+{points} points, +{xp} XP)', 'success')
    return redirect(url_for('assessments'))

@app.route('/resume', methods=['GET', 'POST'])
def resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    
    if request.method == 'POST':
        if 'resume_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['resume_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            unique_filename = timestamp + filename
            
            # Ensure upload directory exists
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Analyze resume
            analysis = analyze_resume(file_path)
            
            # Save resume record
            resume_record = Resume(
                user_id=user.id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                analysis_data=json.dumps(analysis)
            )
            db.session.add(resume_record)
            
            # Award points for resume upload
            activity = Activity(
                user_id=user.id,
                activity_type='resume_upload',
                description='Uploaded and analyzed resume',
                points_earned=40,
                xp_earned=25
            )
            db.session.add(activity)
            
            user.total_points += 40
            user.add_xp(25)
            
            # Check for resume-related badges
            award_badges(user, 'resume', 100)
            
            db.session.commit()
            
            flash('Resume uploaded and analyzed successfully! (+40 points, +25 XP)', 'success')
            return redirect(url_for('resume'))
        else:
            flash('Please upload a PDF, DOC, or DOCX file', 'error')
    
    analysis_data = None
    if user_resume and user_resume.analysis_data:
        analysis_data = json.loads(user_resume.analysis_data)
    
    return render_template('resume.html', 
                         user=user, 
                         resume=user_resume,
                         analysis=analysis_data)

@app.route('/mock_interview', methods=['GET', 'POST'])
def mock_interview():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        responses = {}
        for key, value in request.form.items():
            if key.startswith('response_'):
                question_id = key.replace('response_', '')
                responses[question_id] = value
        
        # Simple scoring based on response length and keywords
        total_score = 0
        feedback_items = []
        
        for response in responses.values():
            score = min(len(response.split()) / 50 * 100, 100)  # Basic scoring
            total_score += score
            if len(response.split()) < 10:
                feedback_items.append("Try to provide more detailed responses")
        
        average_score = total_score / len(responses) if responses else 0
        
        # Save mock interview
        mock_interview_record = MockInterview(
            user_id=user.id,
            questions_data=json.dumps(responses),
            overall_score=average_score,
            feedback=json.dumps(feedback_items)
        )
        db.session.add(mock_interview_record)
        
        # Award points
        points = int(average_score / 2)
        xp = int(average_score / 3)
        
        activity = Activity(
            user_id=user.id,
            activity_type='mock_interview',
            description=f'Completed mock interview (Score: {average_score:.1f}%)',
            points_earned=points,
            xp_earned=xp
        )
        db.session.add(activity)
        
        user.total_points += points
        user.add_xp(xp)
        
        db.session.commit()
        
        flash(f'Mock interview completed! Score: {average_score:.1f}% (+{points} points, +{xp} XP)', 'success')
        return redirect(url_for('mock_interview'))
    
    questions = get_mock_interview_questions()
    previous_interviews = MockInterview.query.filter_by(user_id=user.id).order_by(MockInterview.completed_at.desc()).limit(3).all()
    
    return render_template('mock_interview.html', 
                         user=user, 
                         questions=questions,
                         previous_interviews=previous_interviews)

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Get assessment data for charts
    assessments = Assessment.query.filter_by(user_id=user.id).all()
    
    # Prepare data for charts
    skill_data = {}
    progress_data = []
    
    for assessment in assessments:
        assessment_type = assessment.assessment_type.replace('_', ' ').title()
        percentage = assessment.get_percentage()
        
        if assessment_type not in skill_data:
            skill_data[assessment_type] = []
        skill_data[assessment_type].append({
            'date': assessment.completed_at.strftime('%Y-%m-%d'),
            'score': percentage
        })
    
    # Get recent activities for timeline
    activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.created_at.desc()).limit(10).all()
    
    return render_template('analytics.html', 
                         user=user,
                         skill_data=json.dumps(skill_data),
                         activities=activities)

@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.get(session['user_id'])
    
    # Get top users (only those who opted to show on leaderboard)
    top_users = User.query.filter_by(show_on_leaderboard=True)\
                         .order_by(User.total_xp.desc())\
                         .limit(20).all()
    
    # Find current user's rank
    user_rank = None
    if current_user.show_on_leaderboard:
        higher_xp_count = User.query.filter(
            User.total_xp > current_user.total_xp,
            User.show_on_leaderboard == True
        ).count()
        user_rank = higher_xp_count + 1
    
    return render_template('leaderboard.html', 
                         current_user=current_user,
                         top_users=top_users,
                         user_rank=user_rank)

@app.route('/challenges')
def challenges():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Get user's challenges
    user_challenges = UserChallenge.query.filter_by(user_id=user.id)\
                                        .join(Challenge)\
                                        .order_by(UserChallenge.completed.asc(), UserChallenge.assigned_at.desc())\
                                        .all()
    
    return render_template('challenges.html', 
                         user=user,
                         user_challenges=user_challenges)

# Initialize default data on app startup
def initialize_default_data():
    with app.app_context():
        # Create default badges if they don't exist
        if Badge.query.count() == 0:
            create_default_badges()
        
        # Create default challenges if they don't exist
        if Challenge.query.count() == 0:
            create_default_challenges()

# Call initialization function
initialize_default_data()

# Admin decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Dashboard
@app.route('/admin')
@admin_required
def admin_dashboard():
    user = User.query.get(session['user_id'])
    
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_questions': Question.query.count(),
        'total_assessments': Assessment.query.count(),
        'questions_by_type': {}
    }
    
    # Get questions by type
    for assessment_type in ['aptitude', 'technical', 'soft_skills', 'adaptive']:
        stats['questions_by_type'][assessment_type] = Question.query.filter_by(assessment_type=assessment_type).count()
    
    return render_template('admin_dashboard.html', user=user, stats=stats)

# Admin Questions Management
@app.route('/admin/questions')
@admin_required
def admin_questions():
    user = User.query.get(session['user_id'])
    
    # Get filter parameters
    assessment_type = request.args.get('type', 'all')
    difficulty = request.args.get('difficulty', 'all')
    
    # Build query
    query = Question.query
    if assessment_type != 'all':
        query = query.filter_by(assessment_type=assessment_type)
    if difficulty != 'all':
        query = query.filter_by(difficulty_level=int(difficulty))
    
    questions = query.order_by(Question.assessment_type, Question.difficulty_level, Question.id).all()
    
    return render_template('admin_questions.html', 
                         user=user, 
                         questions=questions,
                         current_type=assessment_type,
                         current_difficulty=difficulty)

# Add Question
@app.route('/admin/questions/add', methods=['GET', 'POST'])
@admin_required
def admin_add_question():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        question_text = request.form['question_text']
        assessment_type = request.form['assessment_type']
        difficulty_level = int(request.form['difficulty_level'])
        category = request.form['category']
        correct_answer = request.form['correct_answer']
        explanation = request.form.get('explanation', '')
        
        # Get options
        options = []
        for i in range(1, 5):
            option = request.form.get(f'option_{i}')
            if option:
                options.append(option.strip())
        
        # Create question
        question = Question(
            question_text=question_text,
            assessment_type=assessment_type,
            difficulty_level=difficulty_level,
            category=category,
            correct_answer=correct_answer,
            explanation=explanation
        )
        question.set_options_list(options)
        
        db.session.add(question)
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin_questions'))
    
    return render_template('admin_add_question.html', user=user)

# Edit Question
@app.route('/admin/questions/edit/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_question(question_id):
    user = User.query.get(session['user_id'])
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        question.question_text = request.form['question_text']
        question.assessment_type = request.form['assessment_type']
        question.difficulty_level = int(request.form['difficulty_level'])
        question.category = request.form['category']
        question.correct_answer = request.form['correct_answer']
        question.explanation = request.form.get('explanation', '')
        
        # Get options
        options = []
        for i in range(1, 5):
            option = request.form.get(f'option_{i}')
            if option:
                options.append(option.strip())
        
        question.set_options_list(options)
        question.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin_questions'))
    
    return render_template('admin_edit_question.html', user=user, question=question)

# Delete Question
@app.route('/admin/questions/delete/<int:question_id>', methods=['POST'])
@admin_required
def admin_delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin_questions'))

# Toggle Question Active Status
@app.route('/admin/questions/toggle/<int:question_id>', methods=['POST'])
@admin_required
def admin_toggle_question(question_id):
    question = Question.query.get_or_404(question_id)
    question.is_active = not question.is_active
    db.session.commit()
    
    status = 'activated' if question.is_active else 'deactivated'
    flash(f'Question {status} successfully!', 'success')
    return redirect(url_for('admin_questions'))

# Admin Levels Management
@app.route('/admin/levels')
@admin_required
def admin_levels():
    user = User.query.get(session['user_id'])
    levels = AssessmentLevel.query.order_by(AssessmentLevel.assessment_type, AssessmentLevel.level_number).all()
    
    return render_template('admin_levels.html', user=user, levels=levels)

# Add Level
@app.route('/admin/levels/add', methods=['GET', 'POST'])
@admin_required
def admin_add_level():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        level = AssessmentLevel(
            assessment_type=request.form['assessment_type'],
            level_number=int(request.form['level_number']),
            level_name=request.form['level_name'],
            description=request.form['description'],
            pass_percentage=float(request.form['pass_percentage']),
            xp_reward=int(request.form['xp_reward']),
            points_reward=int(request.form['points_reward'])
        )
        
        db.session.add(level)
        db.session.commit()
        
        flash('Level added successfully!', 'success')
        return redirect(url_for('admin_levels'))
    
    return render_template('admin_add_level.html', user=user)

# Edit Level
@app.route('/admin/levels/edit/<int:level_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_level(level_id):
    user = User.query.get(session['user_id'])
    level = AssessmentLevel.query.get_or_404(level_id)
    
    if request.method == 'POST':
        level.assessment_type = request.form['assessment_type']
        level.level_number = int(request.form['level_number'])
        level.level_name = request.form['level_name']
        level.description = request.form['description']
        level.pass_percentage = float(request.form['pass_percentage'])
        level.xp_reward = int(request.form['xp_reward'])
        level.points_reward = int(request.form['points_reward'])
        
        db.session.commit()
        
        flash('Level updated successfully!', 'success')
        return redirect(url_for('admin_levels'))
    
    return render_template('admin_edit_level.html', user=user, level=level)

# Delete Level
@app.route('/admin/levels/delete/<int:level_id>', methods=['POST'])
@admin_required
def admin_delete_level(level_id):
    level = AssessmentLevel.query.get_or_404(level_id)
    db.session.delete(level)
    db.session.commit()
    
    flash('Level deleted successfully!', 'success')
    return redirect(url_for('admin_levels'))

# Toggle Level Active Status
@app.route('/admin/levels/toggle/<int:level_id>', methods=['POST'])
@admin_required
def admin_toggle_level(level_id):
    level = AssessmentLevel.query.get_or_404(level_id)
    level.is_active = not level.is_active
    db.session.commit()
    
    status = 'activated' if level.is_active else 'deactivated'
    flash(f'Level {status} successfully!', 'success')
    return redirect(url_for('admin_levels'))

# Create default admin user
@app.route('/admin/create_admin', methods=['GET', 'POST'])
def create_admin():
    # Check if admin already exists
    if User.query.filter_by(is_admin=True).first():
        flash('Admin user already exists', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('create_admin.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('create_admin.html')
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            full_name="Administrator",
            is_admin=True
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        flash('Admin user created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('create_admin.html')
