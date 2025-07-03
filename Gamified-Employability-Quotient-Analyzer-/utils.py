import json
import os
from models import Badge, Challenge, UserBadge, Activity, Assessment, Question, db
from datetime import datetime
import PyPDF2
import textstat
import re
import random

def calculate_employability_score(user):
    """Calculate overall employability score based on various factors"""
    score = 0
    total_weight = 0
    
    # CGPA component (20% weight)
    if user.cgpa > 0:
        cgpa_score = min(user.cgpa / 4.0 * 100, 100)  # Assuming 4.0 scale
        score += cgpa_score * 0.2
        total_weight += 0.2
    
    # Assessment scores (40% weight)
    assessments = Assessment.query.filter_by(user_id=user.id).all()
    if assessments:
        assessment_scores = []
        for assessment in assessments:
            assessment_scores.append(assessment.get_percentage())
        
        avg_assessment_score = sum(assessment_scores) / len(assessment_scores)
        score += avg_assessment_score * 0.4
        total_weight += 0.4
    
    # Resume quality (20% weight)
    if hasattr(user, 'resumes') and user.resumes:
        latest_resume = user.resumes[-1]
        if latest_resume.analysis_data:
            analysis = json.loads(latest_resume.analysis_data)
            resume_score = analysis.get('overall_score', 50)
            score += resume_score * 0.2
            total_weight += 0.2
    
    # Experience/Activities (20% weight)
    activity_count = len(user.activities)
    activity_score = min(activity_count * 5, 100)  # 5 points per activity, max 100
    score += activity_score * 0.2
    total_weight += 0.2
    
    # Normalize the score
    if total_weight > 0:
        final_score = score / total_weight
    else:
        final_score = 0
    
    return round(final_score, 1)

def analyze_resume(file_path):
    """Analyze uploaded resume and return insights"""
    analysis = {
        'word_count': 0,
        'readability_score': 0,
        'sections_found': [],
        'skills_mentioned': [],
        'overall_score': 0,
        'suggestions': []
    }
    
    try:
        # Extract text from PDF
        text = ""
        if file_path.lower().endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        else:
            # For DOC/DOCX files, we'll just return basic analysis
            text = "Sample resume text for analysis"
        
        # Basic analysis
        analysis['word_count'] = len(text.split())
        
        # Check for common resume sections
        sections = ['experience', 'education', 'skills', 'projects', 'certifications']
        for section in sections:
            if section.lower() in text.lower():
                analysis['sections_found'].append(section.title())
        
        # Look for technical skills
        skills = ['python', 'java', 'javascript', 'sql', 'html', 'css', 'react', 'angular', 'node.js']
        for skill in skills:
            if skill.lower() in text.lower():
                analysis['skills_mentioned'].append(skill)
        
        # Calculate overall score
        score = 50  # Base score
        
        if analysis['word_count'] >= 200:
            score += 10
        if analysis['word_count'] >= 400:
            score += 10
        
        score += len(analysis['sections_found']) * 5
        score += len(analysis['skills_mentioned']) * 3
        
        analysis['overall_score'] = min(score, 100)
        
        # Generate suggestions
        if analysis['word_count'] < 200:
            analysis['suggestions'].append("Consider adding more details to reach 200+ words")
        if 'Experience' not in analysis['sections_found']:
            analysis['suggestions'].append("Add an Experience or Work History section")
        if len(analysis['skills_mentioned']) < 3:
            analysis['suggestions'].append("Include more technical skills relevant to your field")
        
    except Exception as e:
        print(f"Error analyzing resume: {e}")
        analysis['suggestions'].append("Unable to fully analyze resume file")
    
    return analysis

def get_assessment_questions(assessment_type):
    """Return questions for different assessment types from database"""
    # Ensure questions are populated in database
    populate_questions_database()
    
    # Get questions from database
    db_questions = Question.get_questions_by_type(assessment_type)
    return [q.to_dict() for q in db_questions]

def get_assessment_questions_legacy(assessment_type):
    """Legacy function - Return questions for different assessment types"""
    questions = {
        'aptitude': [
            {
                'id': 1,
                'question': 'If 3x + 7 = 22, what is the value of x?',
                'options': ['3', '5', '7', '9'],
                'correct': '5'
            },
            {
                'id': 2,
                'question': 'What comes next in the sequence: 2, 6, 12, 20, 30, ?',
                'options': ['40', '42', '44', '46'],
                'correct': '42'
            },
            {
                'id': 3,
                'question': 'A train travels 180 km in 3 hours. What is its average speed?',
                'options': ['50 km/h', '60 km/h', '65 km/h', '70 km/h'],
                'correct': '60 km/h'
            },
            {
                'id': 4,
                'question': 'Which number is the odd one out: 8, 27, 64, 125, 216?',
                'options': ['8', '27', '64', '125'],
                'correct': '8'
            },
            {
                'id': 5,
                'question': 'If COMPUTER is coded as RFUVQNFS, how is MONITOR coded?',
                'options': ['MNITQOP', 'NLMJUPM', 'NPOQMJI', 'NQOJUQM'],
                'correct': 'NQOJUQM'
            }
        ],
        'technical': [
            {
                'id': 1,
                'question': 'Which of the following is NOT a programming language?',
                'options': ['Python', 'Java', 'HTML', 'C++'],
                'correct': 'HTML'
            },
            {
                'id': 2,
                'question': 'What does SQL stand for?',
                'options': ['Structured Query Language', 'Simple Query Language', 'Standard Query Language', 'System Query Language'],
                'correct': 'Structured Query Language'
            },
            {
                'id': 3,
                'question': 'Which data structure follows LIFO (Last In First Out) principle?',
                'options': ['Queue', 'Stack', 'Array', 'Linked List'],
                'correct': 'Stack'
            },
            {
                'id': 4,
                'question': 'What is the time complexity of binary search?',
                'options': ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
                'correct': 'O(log n)'
            },
            {
                'id': 5,
                'question': 'Which HTTP method is used to update a resource?',
                'options': ['GET', 'POST', 'PUT', 'DELETE'],
                'correct': 'PUT'
            }
        ],
        'soft_skills': [
            {
                'id': 1,
                'question': 'When working in a team, what is the most important factor for success?',
                'options': ['Individual brilliance', 'Clear communication', 'Competition among members', 'Working independently'],
                'correct': 'Clear communication'
            },
            {
                'id': 2,
                'question': 'How should you handle constructive criticism?',
                'options': ['Ignore it', 'Get defensive', 'Listen and learn from it', 'Argue back'],
                'correct': 'Listen and learn from it'
            },
            {
                'id': 3,
                'question': 'What is the best way to manage your time effectively?',
                'options': ['Multitask everything', 'Prioritize tasks', 'Work on easy tasks first', 'Avoid planning'],
                'correct': 'Prioritize tasks'
            },
            {
                'id': 4,
                'question': 'In a professional setting, how should you communicate bad news?',
                'options': ['Via email only', 'Be direct and honest', 'Avoid mentioning it', 'Blame others'],
                'correct': 'Be direct and honest'
            },
            {
                'id': 5,
                'question': 'What demonstrates good leadership skills?',
                'options': ['Making all decisions alone', 'Empowering team members', 'Avoiding responsibility', 'Taking all credit'],
                'correct': 'Empowering team members'
            }
        ]
    }
    
    return questions.get(assessment_type, [])

def grade_assessment(assessment_type, answers):
    """Grade the assessment and return score, max_score, and feedback"""
    questions = get_assessment_questions(assessment_type)
    correct_answers = 0
    total_questions = len(questions)
    feedback = []
    
    for question in questions:
        question_id = str(question['id'])
        if question_id in answers:
            if answers[question_id] == question['correct']:
                correct_answers += 1
            else:
                feedback.append(f"Question {question_id}: Correct answer is {question['correct']}")
    
    return correct_answers, total_questions, feedback

def get_adaptive_questions():
    """Return adaptive assessment questions organized by difficulty level"""
    return {
        1: [  # Beginner
            {
                'id': 'a1',
                'question': 'What is 2 + 2?',
                'options': ['3', '4', '5', '6'],
                'correct': '4',
                'difficulty': 1,
                'category': 'basic_math'
            },
            {
                'id': 'a2',
                'question': 'Which is the largest number?',
                'options': ['5', '9', '3', '7'],
                'correct': '9',
                'difficulty': 1,
                'category': 'basic_math'
            },
            {
                'id': 'a3',
                'question': 'What does "communicate" mean?',
                'options': ['To hide information', 'To share information', 'To delete information', 'To lose information'],
                'correct': 'To share information',
                'difficulty': 1,
                'category': 'basic_skills'
            }
        ],
        2: [  # Easy
            {
                'id': 'b1',
                'question': 'If a shirt costs $20 and is 25% off, what is the final price?',
                'options': ['$15', '$16', '$17', '$18'],
                'correct': '$15',
                'difficulty': 2,
                'category': 'math'
            },
            {
                'id': 'b2',
                'question': 'What is the best way to handle workplace conflict?',
                'options': ['Ignore it', 'Discuss it calmly', 'Escalate immediately', 'Gossip about it'],
                'correct': 'Discuss it calmly',
                'difficulty': 2,
                'category': 'soft_skills'
            },
            {
                'id': 'b3',
                'question': 'What is HTML?',
                'options': ['A programming language', 'A markup language', 'A database', 'An operating system'],
                'correct': 'A markup language',
                'difficulty': 2,
                'category': 'basic_tech'
            }
        ],
        3: [  # Medium
            {
                'id': 'c1',
                'question': 'A project requires 6 people working 8 hours a day for 10 days. How many hours total?',
                'options': ['480 hours', '460 hours', '500 hours', '440 hours'],
                'correct': '480 hours',
                'difficulty': 3,
                'category': 'problem_solving'
            },
            {
                'id': 'c2',
                'question': 'What is the most important quality in a team leader?',
                'options': ['Technical expertise', 'Authority', 'Communication skills', 'Speed'],
                'correct': 'Communication skills',
                'difficulty': 3,
                'category': 'leadership'
            },
            {
                'id': 'c3',
                'question': 'What is the time complexity of binary search?',
                'options': ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
                'correct': 'O(log n)',
                'difficulty': 3,
                'category': 'technical'
            }
        ],
        4: [  # Hard
            {
                'id': 'd1',
                'question': 'A company\'s revenue grew from $100k to $150k in one year, then to $200k the next year. What is the compound annual growth rate?',
                'options': ['41.4%', '45.2%', '50.0%', '33.3%'],
                'correct': '41.4%',
                'difficulty': 4,
                'category': 'analytics'
            },
            {
                'id': 'd2',
                'question': 'How would you handle a situation where a team member consistently misses deadlines?',
                'options': ['Fire them immediately', 'Ignore it', 'Have a private conversation to understand and address the issue', 'Publicly criticize them'],
                'correct': 'Have a private conversation to understand and address the issue',
                'difficulty': 4,
                'category': 'management'
            },
            {
                'id': 'd3',
                'question': 'In a distributed system, what is the CAP theorem?',
                'options': ['Consistency, Availability, Partition tolerance', 'Concurrency, Atomicity, Persistence', 'Caching, Authentication, Performance', 'Clustering, Aggregation, Partitioning'],
                'correct': 'Consistency, Availability, Partition tolerance',
                'difficulty': 4,
                'category': 'system_design'
            }
        ],
        5: [  # Expert
            {
                'id': 'e1',
                'question': 'Given a market with elastic demand, how does a 10% price increase affect total revenue?',
                'options': ['Revenue increases', 'Revenue decreases', 'Revenue stays the same', 'Cannot determine'],
                'correct': 'Revenue decreases',
                'difficulty': 5,
                'category': 'economics'
            },
            {
                'id': 'e2',
                'question': 'In organizational psychology, what is the most effective approach to change management?',
                'options': ['Top-down mandates', 'Kotter\'s 8-step process', 'Ignoring resistance', 'Rapid implementation'],
                'correct': 'Kotter\'s 8-step process',
                'difficulty': 5,
                'category': 'psychology'
            },
            {
                'id': 'e3',
                'question': 'What is the space complexity of a recursive solution to the Fibonacci sequence?',
                'options': ['O(1)', 'O(log n)', 'O(n)', 'O(2^n)'],
                'correct': 'O(n)',
                'difficulty': 5,
                'category': 'advanced_tech'
            }
        ]
    }

def get_next_adaptive_question(current_difficulty, correct_streak, total_answered):
    """Get the next question based on adaptive algorithm from database"""
    # Ensure questions are populated
    populate_questions_database()
    
    # Adaptive logic
    if total_answered == 0:
        # Start with easy questions
        current_difficulty = 2
    elif correct_streak >= 2:
        # Increase difficulty after 2 correct answers
        current_difficulty = min(current_difficulty + 1, 5)
    elif correct_streak == 0 and total_answered > 0:
        # Decrease difficulty after wrong answer
        current_difficulty = max(current_difficulty - 1, 1)
    
    # Get questions from database for current difficulty level
    db_questions = Question.get_questions_by_type('adaptive', current_difficulty)
    
    if not db_questions:
        return None, current_difficulty
    
    # Return a random question from the difficulty level
    question_obj = random.choice(db_questions)
    question = question_obj.to_dict()
    
    return question, current_difficulty

def grade_adaptive_assessment(questions_data):
    """Grade adaptive assessment and calculate skill level"""
    total_score = 0
    max_possible = 0
    difficulty_scores = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    difficulty_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for q_data in questions_data:
        difficulty = q_data['difficulty']
        is_correct = q_data['is_correct']
        
        difficulty_counts[difficulty] += 1
        max_possible += difficulty
        
        if is_correct:
            total_score += difficulty
            difficulty_scores[difficulty] += 1
    
    # Calculate overall percentage
    percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
    
    # Determine skill level based on adaptive performance
    if percentage >= 80:
        skill_level = "Expert"
    elif percentage >= 65:
        skill_level = "Advanced"
    elif percentage >= 50:
        skill_level = "Intermediate"
    elif percentage >= 35:
        skill_level = "Beginner"
    else:
        skill_level = "Novice"
    
    # Calculate confidence score based on consistency
    consistency_score = 0
    for diff in range(1, 6):
        if difficulty_counts[diff] > 0:
            accuracy = difficulty_scores[diff] / difficulty_counts[diff]
            consistency_score += accuracy * (diff / 5)  # Weight by difficulty
    
    confidence = min(consistency_score * 100, 100)
    
    return {
        'percentage': percentage,
        'skill_level': skill_level,
        'confidence': confidence,
        'total_score': total_score,
        'max_possible': max_possible,
        'difficulty_breakdown': difficulty_scores
    }

def get_mock_interview_questions():
    """Return mock interview questions"""
    return [
        "Tell me about yourself and your background.",
        "Why are you interested in this field/position?",
        "What are your greatest strengths?",
        "Describe a challenging situation you faced and how you handled it.",
        "Where do you see yourself in 5 years?",
        "Why should we hire you?",
        "What questions do you have for us?"
    ]

def award_badges(user, activity_type, score=None):
    """Award badges based on user activities and achievements"""
    badges_to_award = []
    
    # Assessment-based badges
    if activity_type == 'aptitude' and score and score >= 80:
        badges_to_award.append('Aptitude Pro')
    elif activity_type == 'technical' and score and score >= 80:
        badges_to_award.append('Tech Wizard')
    elif activity_type == 'soft_skills' and score and score >= 80:
        badges_to_award.append('Soft Skills Hero')
    elif activity_type == 'adaptive' and score and score >= 70:
        badges_to_award.append('Adaptive Master')
    elif activity_type == 'resume':
        badges_to_award.append('Resume Ready')
    
    # XP-based badges
    if user.total_xp >= 100 and user.total_xp < 200:
        badges_to_award.append('Rising Star')
    elif user.total_xp >= 500:
        badges_to_award.append('High Achiever')
    
    # Award badges that user doesn't already have
    for badge_name in badges_to_award:
        badge = Badge.query.filter_by(name=badge_name).first()
        if badge:
            existing_user_badge = UserBadge.query.filter_by(
                user_id=user.id, 
                badge_id=badge.id
            ).first()
            
            if not existing_user_badge:
                user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
                db.session.add(user_badge)
                
                # Award XP for earning badge
                user.add_xp(badge.xp_reward)
                
                # Create activity
                activity = Activity(
                    user_id=user.id,
                    activity_type='badge_earned',
                    description=f'Earned "{badge.name}" badge!',
                    xp_earned=badge.xp_reward
                )
                db.session.add(activity)

def create_default_badges():
    """Create default badges for the system"""
    default_badges = [
        {
            'name': 'Welcome Aboard',
            'description': 'Successfully registered and joined the platform',
            'icon': 'fas fa-star',
            'color': 'gold',
            'xp_reward': 25
        },
        {
            'name': 'Aptitude Pro',
            'description': 'Scored 80% or higher on an aptitude test',
            'icon': 'fas fa-brain',
            'color': 'purple',
            'xp_reward': 50
        },
        {
            'name': 'Tech Wizard',
            'description': 'Excelled in technical assessments',
            'icon': 'fas fa-code',
            'color': 'blue',
            'xp_reward': 50
        },
        {
            'name': 'Soft Skills Hero',
            'description': 'Demonstrated excellent soft skills',
            'icon': 'fas fa-handshake',
            'color': 'green',
            'xp_reward': 50
        },
        {
            'name': 'Resume Ready',
            'description': 'Uploaded and optimized resume',
            'icon': 'fas fa-file-alt',
            'color': 'orange',
            'xp_reward': 30
        },
        {
            'name': 'Rising Star',
            'description': 'Earned 100+ XP points',
            'icon': 'fas fa-rocket',
            'color': 'red',
            'xp_reward': 25
        },
        {
            'name': 'High Achiever',
            'description': 'Earned 500+ XP points',
            'icon': 'fas fa-trophy',
            'color': 'gold',
            'xp_reward': 100
        },
        {
            'name': 'Adaptive Master',
            'description': 'Excelled in adaptive employability assessment',
            'icon': 'fas fa-magic',
            'color': 'purple',
            'xp_reward': 75
        }
    ]
    
    for badge_data in default_badges:
        badge = Badge(**badge_data)
        db.session.add(badge)
    
    db.session.commit()

def create_default_challenges():
    """Create default challenges for users"""
    default_challenges = [
        {
            'title': 'Assessment Champion',
            'description': 'Complete any assessment today',
            'challenge_type': 'daily',
            'target_value': 1,
            'xp_reward': 25,
            'points_reward': 15
        },
        {
            'title': 'Profile Perfectionist',
            'description': 'Update your profile information',
            'challenge_type': 'daily',
            'target_value': 1,
            'xp_reward': 15,
            'points_reward': 10
        },
        {
            'title': 'Weekly Warrior',
            'description': 'Complete 3 assessments this week',
            'challenge_type': 'weekly',
            'target_value': 3,
            'xp_reward': 75,
            'points_reward': 50
        },
        {
            'title': 'Resume Master',
            'description': 'Upload your resume this week',
            'challenge_type': 'weekly',
            'target_value': 1,
            'xp_reward': 40,
            'points_reward': 25
        }
    ]
    
    for challenge_data in default_challenges:
        challenge = Challenge(**challenge_data)
        db.session.add(challenge)
    
    db.session.commit()

def populate_questions_database():
    """Populate the database with initial questions"""
    # Check if questions already exist
    if Question.query.first():
        return  # Questions already populated
    
    # Aptitude questions
    aptitude_questions = [
        {
            'question_text': 'If 3x + 7 = 22, what is the value of x?',
            'assessment_type': 'aptitude',
            'difficulty_level': 1,
            'category': 'math',
            'options': ['3', '5', '7', '9'],
            'correct_answer': '5'
        },
        {
            'question_text': 'What comes next in the sequence: 2, 6, 12, 20, 30, ?',
            'assessment_type': 'aptitude',
            'difficulty_level': 1,
            'category': 'sequence',
            'options': ['40', '42', '44', '46'],
            'correct_answer': '42'
        },
        {
            'question_text': 'A train travels 180 km in 3 hours. What is its average speed?',
            'assessment_type': 'aptitude',
            'difficulty_level': 1,
            'category': 'math',
            'options': ['50 km/h', '60 km/h', '65 km/h', '70 km/h'],
            'correct_answer': '60 km/h'
        },
        {
            'question_text': 'Which number is the odd one out: 8, 27, 64, 125, 216?',
            'assessment_type': 'aptitude',
            'difficulty_level': 1,
            'category': 'logic',
            'options': ['8', '27', '64', '125'],
            'correct_answer': '8'
        },
        {
            'question_text': 'If COMPUTER is coded as RFUVQNFS, how is MONITOR coded?',
            'assessment_type': 'aptitude',
            'difficulty_level': 1,
            'category': 'coding',
            'options': ['MNITQOP', 'NLMJUPM', 'NPOQMJI', 'NQOJUQM'],
            'correct_answer': 'NQOJUQM'
        }
    ]
    
    # Technical questions
    technical_questions = [
        {
            'question_text': 'Which of the following is NOT a programming language?',
            'assessment_type': 'technical',
            'difficulty_level': 1,
            'category': 'programming',
            'options': ['Python', 'Java', 'HTML', 'C++'],
            'correct_answer': 'HTML'
        },
        {
            'question_text': 'What does SQL stand for?',
            'assessment_type': 'technical',
            'difficulty_level': 1,
            'category': 'database',
            'options': ['Structured Query Language', 'Simple Query Language', 'Standard Query Language', 'System Query Language'],
            'correct_answer': 'Structured Query Language'
        },
        {
            'question_text': 'Which data structure follows LIFO (Last In First Out) principle?',
            'assessment_type': 'technical',
            'difficulty_level': 1,
            'category': 'data_structures',
            'options': ['Queue', 'Stack', 'Array', 'Linked List'],
            'correct_answer': 'Stack'
        },
        {
            'question_text': 'What is the time complexity of binary search?',
            'assessment_type': 'technical',
            'difficulty_level': 1,
            'category': 'algorithms',
            'options': ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
            'correct_answer': 'O(log n)'
        },
        {
            'question_text': 'Which HTTP method is typically used to update data?',
            'assessment_type': 'technical',
            'difficulty_level': 1,
            'category': 'web',
            'options': ['GET', 'POST', 'PUT', 'DELETE'],
            'correct_answer': 'PUT'
        }
    ]
    
    # Soft skills questions
    soft_skills_questions = [
        {
            'question_text': 'What is the most important aspect of effective communication?',
            'assessment_type': 'soft_skills',
            'difficulty_level': 1,
            'category': 'communication',
            'options': ['Speaking loudly', 'Active listening', 'Using complex words', 'Talking fast'],
            'correct_answer': 'Active listening'
        },
        {
            'question_text': 'How should you handle constructive criticism?',
            'assessment_type': 'soft_skills',
            'difficulty_level': 1,
            'category': 'feedback',
            'options': ['Ignore it', 'Get defensive', 'Listen and learn from it', 'Argue against it'],
            'correct_answer': 'Listen and learn from it'
        },
        {
            'question_text': 'What is the best approach when working in a team?',
            'assessment_type': 'soft_skills',
            'difficulty_level': 1,
            'category': 'teamwork',
            'options': ['Work alone to avoid conflicts', 'Collaborate and communicate openly', 'Take charge of everything', 'Do only your assigned tasks'],
            'correct_answer': 'Collaborate and communicate openly'
        },
        {
            'question_text': 'How do you handle tight deadlines?',
            'assessment_type': 'soft_skills',
            'difficulty_level': 1,
            'category': 'time_management',
            'options': ['Panic and stress', 'Prioritize tasks and manage time effectively', 'Ask for extensions always', 'Work without planning'],
            'correct_answer': 'Prioritize tasks and manage time effectively'
        },
        {
            'question_text': 'What demonstrates good leadership skills?',
            'assessment_type': 'soft_skills',
            'difficulty_level': 1,
            'category': 'leadership',
            'options': ['Making all decisions alone', 'Empowering team members', 'Avoiding responsibility', 'Taking all credit'],
            'correct_answer': 'Empowering team members'
        }
    ]
    
    # Adaptive questions (key ones from each difficulty level)
    adaptive_questions = [
        # Beginner level (1)
        {
            'question_text': 'What is 2 + 2?',
            'assessment_type': 'adaptive',
            'difficulty_level': 1,
            'category': 'basic_math',
            'options': ['3', '4', '5', '6'],
            'correct_answer': '4'
        },
        {
            'question_text': 'Which is the largest number?',
            'assessment_type': 'adaptive',
            'difficulty_level': 1,
            'category': 'basic_math',
            'options': ['5', '9', '3', '7'],
            'correct_answer': '9'
        },
        # Easy level (2)
        {
            'question_text': 'If a shirt costs $20 and is 25% off, what is the final price?',
            'assessment_type': 'adaptive',
            'difficulty_level': 2,
            'category': 'math',
            'options': ['$15', '$16', '$17', '$18'],
            'correct_answer': '$15'
        },
        {
            'question_text': 'What is HTML?',
            'assessment_type': 'adaptive',
            'difficulty_level': 2,
            'category': 'basic_tech',
            'options': ['A programming language', 'A markup language', 'A database', 'An operating system'],
            'correct_answer': 'A markup language'
        },
        # Medium level (3)
        {
            'question_text': 'A project requires 6 people working 8 hours a day for 10 days. How many hours total?',
            'assessment_type': 'adaptive',
            'difficulty_level': 3,
            'category': 'problem_solving',
            'options': ['480 hours', '460 hours', '500 hours', '440 hours'],
            'correct_answer': '480 hours'
        },
        {
            'question_text': 'What is the time complexity of binary search?',
            'assessment_type': 'adaptive',
            'difficulty_level': 3,
            'category': 'technical',
            'options': ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
            'correct_answer': 'O(log n)'
        },
        # Hard level (4)
        {
            'question_text': 'How would you handle a team member who consistently misses deadlines?',
            'assessment_type': 'adaptive',
            'difficulty_level': 4,
            'category': 'management',
            'options': ['Fire them immediately', 'Ignore it', 'Have a private conversation to understand and address the issue', 'Publicly criticize them'],
            'correct_answer': 'Have a private conversation to understand and address the issue'
        },
        {
            'question_text': 'In a distributed system, what is the CAP theorem?',
            'assessment_type': 'adaptive',
            'difficulty_level': 4,
            'category': 'system_design',
            'options': ['Consistency, Availability, Partition tolerance', 'Concurrency, Atomicity, Persistence', 'Caching, Authentication, Performance', 'Clustering, Aggregation, Partitioning'],
            'correct_answer': 'Consistency, Availability, Partition tolerance'
        },
        # Expert level (5)
        {
            'question_text': 'Given a market with elastic demand, how does a 10% price increase affect total revenue?',
            'assessment_type': 'adaptive',
            'difficulty_level': 5,
            'category': 'economics',
            'options': ['Revenue increases', 'Revenue decreases', 'Revenue stays the same', 'Cannot determine'],
            'correct_answer': 'Revenue decreases'
        },
        {
            'question_text': 'What is the space complexity of a recursive Fibonacci solution?',
            'assessment_type': 'adaptive',
            'difficulty_level': 5,
            'category': 'advanced_tech',
            'options': ['O(1)', 'O(log n)', 'O(n)', 'O(2^n)'],
            'correct_answer': 'O(n)'
        }
    ]
    
    # Combine all questions
    all_questions = aptitude_questions + technical_questions + soft_skills_questions + adaptive_questions
    
    # Add questions to database
    for q_data in all_questions:
        question = Question(
            question_text=q_data['question_text'],
            assessment_type=q_data['assessment_type'],
            difficulty_level=q_data['difficulty_level'],
            category=q_data['category'],
            correct_answer=q_data['correct_answer']
        )
        question.set_options_list(q_data['options'])
        db.session.add(question)
    
    db.session.commit()
    print(f"Added {len(all_questions)} questions to database")
