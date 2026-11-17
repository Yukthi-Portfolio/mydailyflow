from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class Assignment(db.Model):
    """Model for storing student assignments"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High
    status = db.Column(db.String(20), default='Pending')  # Pending, Completed
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Assignment {self.title}>'

class Habit(db.Model):
    """Model for storing daily habits"""
    id = db.Column(db.Integer, primary_key=True)
    habit_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Study, Health, Productivity
    target_frequency = db.Column(db.String(20), default='Daily')  # Daily, Weekly
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    is_completed_today = db.Column(db.Boolean, default=False)
    last_completed = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Habit {self.habit_name}>'

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Dashboard - Shows overview of assignments and habits"""
    # Get today's date
    today = datetime.now().date()
    
    # Get pending assignments
    pending_assignments = Assignment.query.filter_by(status='Pending').order_by(Assignment.due_date).all()
    
    # Get assignments due today
    assignments_due_today = Assignment.query.filter(
        Assignment.due_date == today,
        Assignment.status == 'Pending'
    ).all()
    
    # Get all habits
    habits = Habit.query.all()
    
    # Calculate habit completion for today
    habits_completed_today = sum(1 for h in habits if h.is_completed_today)
    total_habits = len(habits)
    
    # Get recent assignments (last 5)
    recent_assignments = Assignment.query.order_by(Assignment.created_at.desc()).limit(5).all()
    
    return render_template('index.html',
    pending_assignments=pending_assignments,
    assignments_due_today=assignments_due_today,
    habits=habits,
    habits_completed_today=habits_completed_today,
    total_habits=total_habits,
    recent_assignments=recent_assignments,
    today=today)

# ==================== ASSIGNMENT ROUTES (CRUD) ====================

@app.route('/assignments')
def assignments():
    """READ - View all assignments"""
    today = datetime.now().date()
    all_assignments = Assignment.query.order_by(Assignment.due_date).all()
    pending_count = Assignment.query.filter_by(status='Pending').count()
    completed_count = Assignment.query.filter_by(status='Completed').count()
    
    return render_template('assignments.html',
    assignments=all_assignments,
    pending_count=pending_count,
    completed_count=completed_count,
    today=today)

@app.route('/add-assignment', methods=['GET', 'POST'])
def add_assignment():
    """CREATE - Add new assignment"""
    if request.method == 'POST':
        title = request.form['title']
        subject = request.form['subject']
        due_date_str = request.form['due_date']
        priority = request.form['priority']
        description = request.form.get('description', '')
        
        # Convert string date to date object
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        
        # Create new assignment
        new_assignment = Assignment(
            title=title,
            subject=subject,
            due_date=due_date,
            priority=priority,
            description=description
        )
        
        try:
            db.session.add(new_assignment)
            db.session.commit()
            flash('Assignment added successfully!', 'success')
            return redirect(url_for('assignments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding assignment: {str(e)}', 'error')
            return redirect(url_for('add_assignment'))
    
    return render_template('add_assignment.html')

@app.route('/edit-assignment/<int:id>', methods=['GET', 'POST'])
def edit_assignment(id):
    """UPDATE - Edit existing assignment"""
    assignment = Assignment.query.get_or_404(id)
    
    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.subject = request.form['subject']
        assignment.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        assignment.priority = request.form['priority']
        assignment.status = request.form['status']
        assignment.description = request.form.get('description', '')
        
        try:
            db.session.commit()
            flash('Assignment updated successfully!', 'success')
            return redirect(url_for('assignments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating assignment: {str(e)}', 'error')
    
    return render_template('edit_assignment.html', assignment=assignment)

@app.route('/delete-assignment/<int:id>')
def delete_assignment(id):
    """DELETE - Remove assignment"""
    assignment = Assignment.query.get_or_404(id)
    
    try:
        db.session.delete(assignment)
        db.session.commit()
        flash('Assignment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting assignment: {str(e)}', 'error')
    
    return redirect(url_for('assignments'))

@app.route('/toggle-assignment/<int:id>')
def toggle_assignment(id):
    """Toggle assignment completion status"""
    assignment = Assignment.query.get_or_404(id)
    
    if assignment.status == 'Pending':
        assignment.status = 'Completed'
    else:
        assignment.status = 'Pending'
    
    try:
        db.session.commit()
        flash('Assignment status updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'error')
    
    return redirect(url_for('assignments'))

# ==================== HABIT ROUTES (CRUD) ====================

@app.route('/habits')
def habits():
    """READ - View all habits"""
    all_habits = Habit.query.order_by(Habit.created_at.desc()).all()
    
    # Calculate statistics
    total_habits = len(all_habits)
    completed_today = sum(1 for h in all_habits if h.is_completed_today)
    
    return render_template('habits.html',
                         habits=all_habits,
                         total_habits=total_habits,
                         completed_today=completed_today)

@app.route('/add-habit', methods=['GET', 'POST'])
def add_habit():
    """CREATE - Add new habit"""
    if request.method == 'POST':
        habit_name = request.form['habit_name']
        category = request.form['category']
        target_frequency = request.form['target_frequency']
        
        # Create new habit
        new_habit = Habit(
            habit_name=habit_name,
            category=category,
            target_frequency=target_frequency
        )
        
        try:
            db.session.add(new_habit)
            db.session.commit()
            flash('Habit added successfully!', 'success')
            return redirect(url_for('habits'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding habit: {str(e)}', 'error')
            return redirect(url_for('add_habit'))
    
    return render_template('add_habit.html')

@app.route('/edit-habit/<int:id>', methods=['GET', 'POST'])
def edit_habit(id):
    """UPDATE - Edit existing habit"""
    habit = Habit.query.get_or_404(id)
    
    if request.method == 'POST':
        habit.habit_name = request.form['habit_name']
        habit.category = request.form['category']
        habit.target_frequency = request.form['target_frequency']
        
        try:
            db.session.commit()
            flash('Habit updated successfully!', 'success')
            return redirect(url_for('habits'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating habit: {str(e)}', 'error')
    
    return render_template('edit_habit.html', habit=habit)

@app.route('/delete-habit/<int:id>')
def delete_habit(id):
    """DELETE - Remove habit"""
    habit = Habit.query.get_or_404(id)
    
    try:
        db.session.delete(habit)
        db.session.commit()
        flash('Habit deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting habit: {str(e)}', 'error')
    
    return redirect(url_for('habits'))

@app.route('/toggle-habit/<int:id>')
def toggle_habit(id):
    """Toggle habit completion for today"""
    habit = Habit.query.get_or_404(id)
    today = datetime.now().date()
    
    if habit.is_completed_today:
        # Unmark as completed
        habit.is_completed_today = False
        if habit.current_streak > 0:
            habit.current_streak -= 1
    else:
        # Mark as completed
        habit.is_completed_today = True
        habit.last_completed = today
        habit.current_streak += 1
        
        # Update longest streak if needed
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
    
    try:
        db.session.commit()
        flash('Habit status updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating habit: {str(e)}', 'error')
    
    return redirect(url_for('habits'))

# ==================== INITIALIZE DATABASE ====================

def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    # Create database tables if they don't exist
    init_db()
    
    # Run the Flask app
    app.run(debug=True, port=5001)