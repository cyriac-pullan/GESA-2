# Employability Game - Replit Project Documentation

## Overview

The Employability Game is a gamified web application designed to help students assess and improve their employability skills. Built with Flask and SQLAlchemy, it transforms career development into an engaging gaming experience where users can take assessments, earn XP, unlock badges, and track their progress through various skill categories.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite (development) and PostgreSQL (production)
- **Authentication**: Session-based authentication using Flask sessions
- **File Processing**: PyPDF2 for PDF resume analysis, python-docx for Word documents
- **Text Analysis**: NLTK and textstat for resume content analysis
- **Data Analysis**: pandas and numpy for analytics processing

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default templating)
- **CSS Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Charts**: Chart.js with date-fns adapter
- **Styling**: Custom CSS with gaming-inspired theme and gradients

### Database Schema
- **Users**: Core user information with gamification fields (XP, level, points)
- **Assessments**: Skill assessment results and scoring
- **Badges**: Achievement system with earned badges tracking
- **Activities**: User activity logging for engagement tracking
- **Resumes**: File upload and analysis data storage
- **Challenges**: Daily/weekly challenges system
- **Mock Interviews**: Interview practice and feedback system

## Key Components

### User Management System
- Registration and authentication with academic profile data
- Session management for user state persistence
- Profile customization with privacy settings (leaderboard visibility)
- Academic information tracking (CGPA, major, year of study)

### Gamification Engine
- **XP System**: Experience points for completed activities
- **Level Progression**: Beginner → Learning → Almost Ready → Ready
- **Badge System**: Achievements for various milestones
- **Leaderboard**: Competitive ranking system with privacy controls
- **Challenge System**: Daily and weekly tasks for extra engagement

### Assessment System
- **Multiple Categories**: Aptitude, Technical, Soft Skills
- **Dynamic Scoring**: Percentage-based grading with XP rewards
- **Question Bank**: Structured question storage with multiple choice options
- **Progress Tracking**: Historical assessment performance

### Resume Analysis
- **File Upload**: Support for PDF and Word documents
- **Content Analysis**: Text extraction and quality assessment
- **Scoring System**: Comprehensive resume evaluation
- **Feedback Generation**: Detailed analysis with improvement suggestions

### Analytics Dashboard
- **Performance Metrics**: Employability score calculation
- **Progress Visualization**: Charts and graphs using Chart.js
- **Skill Radar**: Multi-dimensional skill assessment display
- **Trend Analysis**: Progress tracking over time

## Data Flow

### User Registration Flow
1. User submits registration form with academic details
2. Password hashing using Werkzeug security
3. User record creation in database
4. Welcome activity logging
5. Default challenges assignment

### Assessment Flow
1. User selects assessment type
2. Dynamic question loading from database
3. Timed assessment with JavaScript timer
4. Answer submission and scoring
5. XP calculation and badge checking
6. Results display with performance analysis

### Resume Analysis Flow
1. File upload with security validation
2. Text extraction based on file type
3. Content analysis using NLTK and textstat
4. Scoring algorithm application
5. Analysis data storage as JSON
6. Employability score recalculation

## External Dependencies

### Python Packages
- **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Database**: psycopg2-binary (PostgreSQL), SQLAlchemy
- **File Processing**: PyPDF2, python-docx
- **Text Analysis**: NLTK, textstat, scikit-learn
- **Data Processing**: pandas, numpy
- **Security**: Werkzeug, email-validator
- **Environment**: python-dotenv

### Frontend Libraries
- **Bootstrap 5.3.0**: Responsive UI framework
- **Font Awesome 6.4.0**: Icon library
- **Chart.js**: Data visualization
- **chartjs-adapter-date-fns**: Date handling for charts

### Production Dependencies
- **WSGI Server**: Gunicorn for production deployment
- **Proxy Support**: ProxyFix middleware for reverse proxy compatibility

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database, debug mode enabled
- **Production**: PostgreSQL database, environment variables for sensitive data
- **File Storage**: Local uploads directory with size limits (16MB max)

### Security Measures
- **Password Hashing**: Werkzeug's generate_password_hash
- **Session Management**: Flask's built-in session handling
- **File Upload Security**: Secure filename handling and type validation
- **Database Security**: Parameterized queries through SQLAlchemy ORM

### Scalability Considerations
- **Database Connection Pooling**: Configured with pool_recycle and pool_pre_ping
- **Static File Serving**: Separate static directory for CSS/JS assets
- **Session Storage**: Server-side session management

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- July 03, 2025. Initial setup