import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
import mysql.connector
import random
import string
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

# Database Connection Helper
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "clinic_appointment_db"),
        port=int(os.environ.get("DB_PORT", 3306))
    )

# Decorators for Role-Based Access Control
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'employee_id' not in session and 'admin_id' not in session:
            flash('Please log in first.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'doctor':
            flash('Doctor/Staff access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'user':
            flash('Patient access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('landing.html', services=services)

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if login_type == 'user' or login_type == 'admin':
            email = request.form.get('email')
            password = request.form.get('password')
            
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s AND role = %s", (email, password, login_type))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['name'] = user['name']
                flash('Login successful!', 'success')
                
                if login_type == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
                
        elif login_type == 'employee':
            employee_tag = request.form.get('employee_tag')
            cursor.execute("SELECT * FROM employees WHERE employee_tag = %s", (employee_tag,))
            employee = cursor.fetchone()
            
            if employee:
                session['employee_id'] = employee['id']
                session['role'] = 'doctor'
                session['name'] = employee['name']
                flash('Login successful!', 'success')
                return redirect(url_for('doctor_dashboard'))
            else:
                flash('Invalid employee tag.', 'danger')
                
        cursor.close()
        conn.close()

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if email exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already exists. Please login.', 'danger')
        else:
            cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'user')", (name, email, password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
            
        cursor.close()
        conn.close()
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            # Generate 6-digit code
            code = ''.join(random.choices(string.digits, k=6))
            expiry = datetime.now() + timedelta(minutes=15)
            
            # Store in DB
            cursor.execute("UPDATE users SET reset_code = %s, reset_code_expiry = %s WHERE id = %s", (code, expiry, user['id']))
            conn.commit()
            
            # Simulate email sending
            print(f"\n=======================================================")
            print(f"EMAIL SIMULATION: Password Reset Code for {email}")
            print(f"Your 6-digit verification code is: {code}")
            print(f"=======================================================\n")
            
            session['reset_email'] = email
            flash(f'A reset code has been sent to {email}. (Check terminal console for simulation)', 'info')
            
            cursor.close()
            conn.close()
            return redirect(url_for('verify_reset_code'))
            
        else:
            flash('Email address not found.', 'danger')
            
        cursor.close()
        conn.close()
        
    return render_template('forgot_password.html')

@app.route('/verify-reset-code', methods=['GET', 'POST'])
def verify_reset_code():
    if 'reset_email' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        code = request.form.get('reset_code')
        email = session.get('reset_email')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, reset_code, reset_code_expiry FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and user['reset_code'] == code:
            if user['reset_code_expiry'] and user['reset_code_expiry'] > datetime.now():
                session['reset_authorized'] = True
                cursor.close()
                conn.close()
                return redirect(url_for('reset_password'))
            else:
                flash('The reset code has expired. Please request a new one.', 'danger')
        else:
            flash('Invalid reset code.', 'danger')
            
        cursor.close()
        conn.close()
        
    return render_template('verify_reset_code.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_authorized') or 'reset_email' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html')
            
        email = session.get('reset_email')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET password = %s, reset_code = NULL, reset_code_expiry = NULL WHERE email = %s", 
            (new_password, email)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        session.pop('reset_email', None)
        session.pop('reset_authorized', None)
        
        flash('Your password has been successfully reset. Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')

@app.route('/user/dashboard')
@user_required
def user_dashboard():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.*, s.service_name, e.name as doctor_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN employees e ON a.employee_id = e.id
        WHERE a.user_id = %s
        ORDER BY a.date DESC, a.time DESC
    """, (user_id,))
    appointments = cursor.fetchall()
    
    # Format times for display
    from datetime import datetime
    for appt in appointments:
        t_str = str(appt['time'])
        end_t_str = str(appt['end_time'])
        if len(t_str.split(':')) == 2: t_str += ':00'
        if len(end_t_str.split(':')) == 2: end_t_str += ':00'
        try:
            time_obj = datetime.strptime(t_str, '%H:%M:%S')
            end_time_obj = datetime.strptime(end_t_str, '%H:%M:%S')
            appt['display_time'] = time_obj.strftime('%I:%M %p') + ' - ' + end_time_obj.strftime('%I:%M %p')
        except ValueError:
            appt['display_time'] = t_str + ' - ' + end_t_str
    
    # Also fetch user's pending requests to disable buttons
    cursor.execute("""
        SELECT appointment_id, request_type 
        FROM appointment_requests 
        WHERE appointment_id IN (SELECT id FROM appointments WHERE user_id = %s)
        AND status = 'Pending'
    """, (user_id,))
    pending_reqs = cursor.fetchall()
    
    # Create a set of appointment IDs that have pending requests
    pending_cancel = set(r['appointment_id'] for r in pending_reqs if r['request_type'] == 'Cancel')
    pending_reschedule = set(r['appointment_id'] for r in pending_reqs if r['request_type'] == 'Reschedule')
    
    cursor.close()
    conn.close()
    return render_template('user_dashboard.html', appointments=appointments, 
                           pending_cancel=pending_cancel, pending_reschedule=pending_reschedule)

@app.route('/user/appointment/<int:id>/request_cancel')
@user_required
def request_cancel(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointment_requests (appointment_id, request_type) VALUES (%s, 'Cancel')", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Cancellation requested successfully. Waiting for admin approval.', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/appointment/<int:id>/reschedule', methods=['GET', 'POST'])
@user_required
def request_reschedule(id):
    from datetime import date, timedelta, datetime
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get appointment details to find doctor
    cursor.execute("SELECT * FROM appointments WHERE id = %s AND user_id = %s", (id, session.get('user_id')))
    appt = cursor.fetchone()
    
    if not appt:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('user_dashboard'))
        
    employee_id = appt['employee_id']
    
    if request.method == 'POST':
        slot_data = request.form.get('slot').split('|')
        new_date = slot_data[0]
        new_time = slot_data[1]
        new_end_time = slot_data[2]
        
        cursor.execute("""
            INSERT INTO appointment_requests (appointment_id, request_type, requested_date, requested_time, requested_end_time) 
            VALUES (%s, 'Reschedule', %s, %s, %s)
        """, (id, new_date, new_time, new_end_time))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Reschedule requested successfully. Waiting for admin approval.', 'success')
        return redirect(url_for('user_dashboard'))

    # Load slots for reschedule GET request
    cursor.execute("SELECT day_of_week, time, end_time FROM employee_schedules WHERE employee_id = %s", (employee_id,))
    schedules = cursor.fetchall()
    
    cursor.execute("SELECT date, time FROM appointments WHERE employee_id = %s AND status != 'Cancelled'", (employee_id,))
    booked_appointments = cursor.fetchall()
    
    booked_set = set()
    for b in booked_appointments:
        d_str = b['date'].strftime('%Y-%m-%d') if isinstance(b['date'], date) else str(b['date'])
        t_str = str(b['time'])
        if len(t_str.split(':')) == 2: t_str += ':00'
        booked_set.add(f"{d_str}|{t_str}")
        
    slots_by_date = {}
    day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    today = date.today()
    
    for i in range(1, 31):
        check_date = today + timedelta(days=i)
        day_name = day_map[check_date.weekday()]
        
        for sched in schedules:
            if sched['day_of_week'] == day_name:
                t_str = str(sched['time'])
                if len(t_str.split(':')) == 2: t_str += ':00'
                end_t_str = str(sched['end_time'])
                if len(end_t_str.split(':')) == 2: end_t_str += ':00'
                d_str = check_date.strftime('%Y-%m-%d')
                slot_key = f"{d_str}|{t_str}"
                
                if slot_key not in booked_set:
                    display_date = check_date.strftime('%A, %B %d, %Y')
                    if display_date not in slots_by_date: slots_by_date[display_date] = []
                    time_obj = datetime.strptime(t_str, '%H:%M:%S')
                    end_time_obj = datetime.strptime(end_t_str, '%H:%M:%S')
                    display_time = time_obj.strftime('%I:%M %p') + ' - ' + end_time_obj.strftime('%I:%M %p')
                    slots_by_date[display_date].append({'date_val': d_str, 'time_val': t_str, 'end_time_val': end_t_str, 'display_time': display_time})
                    
    for d in slots_by_date:
        slots_by_date[d] = sorted(slots_by_date[d], key=lambda x: x['time_val'])
        
    cursor.close()
    conn.close()
    
    return render_template('request_reschedule.html', appt=appt, slots_by_date=slots_by_date)

@app.route('/book/step1', methods=['GET', 'POST'])
@user_required
def book_step1():
    if request.method == 'POST':
        session['booking_category_id'] = request.form.get('category_id')
        return redirect(url_for('book_step2'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM service_categories")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('book_step1.html', categories=categories)

@app.route('/book/step2', methods=['GET', 'POST'])
@user_required
def book_step2():
    if 'booking_category_id' not in session:
        return redirect(url_for('book_step1'))
        
    if request.method == 'POST':
        session['booking_service_id'] = request.form.get('service_id')
        return redirect(url_for('book_step3'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM services WHERE category_id = %s", (session['booking_category_id'],))
    services = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('book_step2.html', services=services)

@app.route('/book/step3', methods=['GET', 'POST'])
@user_required
def book_step3():
    if 'booking_service_id' not in session:
        return redirect(url_for('book_step2'))
        
    if request.method == 'POST':
        session['booking_employee_id'] = request.form.get('employee_id')
        return redirect(url_for('book_step4'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.* 
        FROM employees e 
        JOIN employee_services es ON e.id = es.employee_id 
        WHERE es.service_id = %s
    """, (session['booking_service_id'],))
    doctors = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('book_step3.html', doctors=doctors)

@app.route('/book/step4', methods=['GET', 'POST'])
@user_required
def book_step4():
    from datetime import date, timedelta, datetime
    if 'booking_employee_id' not in session:
        return redirect(url_for('book_step3'))
        
    if request.method == 'POST':
        slot_data = request.form.get('slot').split('|')
        session['booking_date'] = slot_data[0]
        session['booking_time'] = slot_data[1]
        session['booking_end_time'] = slot_data[2]
        return redirect(url_for('book_step5'))
        
    employee_id = session['booking_employee_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get doctor schedules
    cursor.execute("SELECT day_of_week, time, end_time FROM employee_schedules WHERE employee_id = %s", (employee_id,))
    schedules = cursor.fetchall()
    
    # Get existing appointments to block them
    cursor.execute("SELECT date, time FROM appointments WHERE employee_id = %s AND status != 'Cancelled'", (employee_id,))
    booked_appointments = cursor.fetchall()
    
    booked_set = set()
    for b in booked_appointments:
        # Format date as YYYY-MM-DD
        d_str = b['date'].strftime('%Y-%m-%d') if isinstance(b['date'], date) else str(b['date'])
        # Time delta to string
        t_str = str(b['time'])
        if len(t_str.split(':')) == 2:
            t_str += ':00' # Handle HH:MM
        booked_set.add(f"{d_str}|{t_str}")
        
    slots_by_date = {}
    day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    
    today = date.today()
    
    for i in range(1, 31): # Next 30 days
        check_date = today + timedelta(days=i)
        day_name = day_map[check_date.weekday()]
        
        for sched in schedules:
            if sched['day_of_week'] == day_name:
                t_str = str(sched['time'])
                if len(t_str.split(':')) == 2:
                    t_str += ':00'
                end_t_str = str(sched['end_time'])
                if len(end_t_str.split(':')) == 2:
                    end_t_str += ':00'
                    
                d_str = check_date.strftime('%Y-%m-%d')
                slot_key = f"{d_str}|{t_str}"
                
                if slot_key not in booked_set:
                    display_date = check_date.strftime('%A, %B %d, %Y')
                    if display_date not in slots_by_date:
                        slots_by_date[display_date] = []
                    
                    # Format time nicely for UI
                    time_obj = datetime.strptime(t_str, '%H:%M:%S')
                    end_time_obj = datetime.strptime(end_t_str, '%H:%M:%S')
                    display_time = time_obj.strftime('%I:%M %p') + ' - ' + end_time_obj.strftime('%I:%M %p')
                    
                    slots_by_date[display_date].append({
                        'date_val': d_str,
                        'time_val': t_str,
                        'end_time_val': end_t_str,
                        'display_time': display_time
                    })
                    
    # Sort slots by time
    for d in slots_by_date:
        slots_by_date[d] = sorted(slots_by_date[d], key=lambda x: x['time_val'])
        
    cursor.close()
    conn.close()
    
    return render_template('book_step4.html', slots_by_date=slots_by_date)

@app.route('/book/step5', methods=['GET', 'POST'])
@user_required
def book_step5():
    import string, random
    if 'booking_time' not in session:
        return redirect(url_for('book_step4'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        user_id = session.get('user_id')
        employee_id = session['booking_employee_id']
        service_id = session['booking_service_id']
        date = session['booking_date']
        time = session['booking_time']
        end_time = session.get('booking_end_time', '00:00:00')
        
        patient_name = request.form.get('patient_name')
        patient_age = request.form.get('patient_age')
        patient_gender = request.form.get('patient_gender')
        patient_contact = request.form.get('patient_contact')
        
        # Get service price
        cursor.execute("SELECT price FROM services WHERE id = %s", (service_id,))
        service = cursor.fetchone()
        amount = service['price'] if service else 0.0
        
        # Generate reference number
        ref_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        cursor.execute("""
            INSERT INTO appointments 
            (user_id, employee_id, service_id, date, time, end_time, reference_number, 
             patient_name, patient_age, patient_gender, patient_contact, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, employee_id, service_id, date, time, end_time, ref_num, 
              patient_name, patient_age, patient_gender, patient_contact, amount))
        
        conn.commit()
        appointment_id = cursor.lastrowid
        
        # Clear booking session data
        for key in ['booking_category_id', 'booking_service_id', 'booking_employee_id', 'booking_date', 'booking_time', 'booking_end_time']:
            session.pop(key, None)
            
        cursor.close()
        conn.close()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('receipt', id=appointment_id))
        
    # Get summary data for confirmation view
    cursor.execute("SELECT service_name, price FROM services WHERE id = %s", (session['booking_service_id'],))
    service = cursor.fetchone()
    cursor.execute("SELECT name FROM employees WHERE id = %s", (session['booking_employee_id'],))
    doctor = cursor.fetchone()
    
    from datetime import datetime
    try:
        t_obj = datetime.strptime(session['booking_time'], '%H:%M:%S')
        end_obj = datetime.strptime(session.get('booking_end_time', '00:00:00'), '%H:%M:%S')
        display_time = t_obj.strftime('%I:%M %p') + ' - ' + end_obj.strftime('%I:%M %p')
    except ValueError:
        display_time = session['booking_time'] + ' - ' + session.get('booking_end_time', '')
        
    cursor.close()
    conn.close()
    
    return render_template('book_step5.html', service=service, doctor=doctor, display_time=display_time)

@app.route('/receipt/<int:id>')
@user_required
def receipt(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.*, s.service_name, e.name as doctor_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN employees e ON a.employee_id = e.id
        WHERE a.id = %s AND a.user_id = %s
    """, (id, session.get('user_id')))
    
    appt = cursor.fetchone()
    
    if appt:
        from datetime import datetime
        t_str = str(appt['time'])
        end_t_str = str(appt['end_time'])
        if len(t_str.split(':')) == 2: t_str += ':00'
        if len(end_t_str.split(':')) == 2: end_t_str += ':00'
        try:
            time_obj = datetime.strptime(t_str, '%H:%M:%S')
            end_time_obj = datetime.strptime(end_t_str, '%H:%M:%S')
            appt['display_time'] = time_obj.strftime('%I:%M %p') + ' - ' + end_time_obj.strftime('%I:%M %p')
        except ValueError:
            appt['display_time'] = t_str + ' - ' + end_t_str
    cursor.close()
    conn.close()
    
    if not appt:
        flash('Receipt not found.', 'danger')
        return redirect(url_for('user_dashboard'))
        
    return render_template('receipt.html', appt=appt)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, a.reference_number, a.patient_name, a.date, a.time, a.end_time, a.status, 
               e.name as doctor_name, s.service_name
        FROM appointments a
        JOIN employees e ON a.employee_id = e.id
        JOIN services s ON a.service_id = s.id
        ORDER BY a.date DESC, a.time DESC
    """)
    appointments = cursor.fetchall()
    
    from datetime import datetime
    for appt in appointments:
        t_str = str(appt['time'])
        end_t_str = str(appt['end_time'])
        if len(t_str.split(':')) == 2: t_str += ':00'
        if len(end_t_str.split(':')) == 2: end_t_str += ':00'
        try:
            time_obj = datetime.strptime(t_str, '%H:%M:%S')
            end_time_obj = datetime.strptime(end_t_str, '%H:%M:%S')
            appt['display_time'] = time_obj.strftime('%I:%M %p') + ' - ' + end_time_obj.strftime('%I:%M %p')
        except ValueError:
            appt['display_time'] = t_str + ' - ' + end_t_str
            
    # Get pending requests
    cursor.execute("""
        SELECT r.id, r.appointment_id, r.request_type, r.requested_date, r.requested_time, r.requested_end_time, r.status,
               a.reference_number, a.patient_name, a.date as old_date, a.time as old_time, a.end_time as old_end_time
        FROM appointment_requests r
        JOIN appointments a ON r.appointment_id = a.id
        WHERE r.status = 'Pending'
    """)
    requests = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', appointments=appointments, requests=requests)

@app.route('/admin/request/<int:id>/<action>')
@admin_required
def admin_request_action(id, action):
    if action not in ['approve', 'reject']:
        return redirect(url_for('admin_dashboard'))
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM appointment_requests WHERE id = %s", (id,))
    req = cursor.fetchone()
    
    if not req or req['status'] != 'Pending':
        cursor.close()
        conn.close()
        flash('Request not found or already processed.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    if action == 'approve':
        if req['request_type'] == 'Cancel':
            cursor.execute("UPDATE appointments SET status = 'Cancelled' WHERE id = %s", (req['appointment_id'],))
        elif req['request_type'] == 'Reschedule':
            cursor.execute("UPDATE appointments SET date = %s, time = %s, end_time = %s WHERE id = %s", 
                           (req['requested_date'], req['requested_time'], req['requested_end_time'], req['appointment_id']))
        cursor.execute("UPDATE appointment_requests SET status = 'Approved' WHERE id = %s", (id,))
        flash('Request approved successfully.', 'success')
    else:
        cursor.execute("UPDATE appointment_requests SET status = 'Rejected' WHERE id = %s", (id,))
        flash('Request rejected.', 'success')
        
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/appointment/<int:id>/<action>')
@admin_required
def admin_appointment_action(id, action):
    if action not in ['approve', 'cancel']:
        return redirect(url_for('admin_dashboard'))
        
    status_map = {'approve': 'Approved', 'cancel': 'Cancelled'}
    new_status = status_map[action]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE appointments SET status = %s WHERE id = %s", (new_status, id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f'Appointment {new_status} successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/appointment/edit/<int:id>', methods=['POST'])
@admin_required
def edit_appointment(id):
    date = request.form.get('date')
    time = request.form.get('time')
    end_time = request.form.get('end_time', '00:00:00')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE appointments SET date = %s, time = %s, end_time = %s WHERE id = %s", (date, time, end_time, id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Appointment edited successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/appointment/delete/<int:id>')
@admin_required
def delete_appointment(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Appointment deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/services', methods=['GET', 'POST'])
@admin_required
def admin_services():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        description = request.form.get('description')
        price = request.form.get('price')
        category_id = request.form.get('category_id')
        
        cursor.execute("INSERT INTO services (service_name, description, price, category_id) VALUES (%s, %s, %s, %s)",
                       (service_name, description, price, category_id))
        conn.commit()
        flash('Service added successfully.', 'success')
        
    cursor.execute("""
        SELECT s.*, c.name as category_name 
        FROM services s
        LEFT JOIN service_categories c ON s.category_id = c.id
    """)
    services = cursor.fetchall()
    
    cursor.execute("SELECT * FROM service_categories")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_services.html', services=services, categories=categories)

@app.route('/admin/service/delete/<int:id>')
@admin_required
def delete_service(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Service deleted successfully.', 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/service/edit/<int:id>', methods=['POST'])
@admin_required
def edit_service(id):
    service_name = request.form.get('service_name')
    description = request.form.get('description')
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE services SET service_name = %s, description = %s, price = %s, category_id = %s WHERE id = %s",
                   (service_name, description, price, category_id, id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Service updated successfully.', 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories_page():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO service_categories (name, description) VALUES (%s, %s)", (name, description))
        conn.commit()
        cursor.close()
        flash('Category added successfully.', 'success')
        return redirect(url_for('admin_categories_page'))
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM service_categories")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_categories.html', categories=categories)

@app.route('/admin/category/edit/<int:id>', methods=['POST'])
@admin_required
def edit_category(id):
    name = request.form.get('name')
    description = request.form.get('description')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE service_categories SET name = %s, description = %s WHERE id = %s", (name, description, id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Category updated successfully.', 'success')
    return redirect(url_for('admin_categories_page'))

@app.route('/admin/category/delete/<int:id>')
@admin_required
def delete_category(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM service_categories WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin_categories_page'))

@app.route('/admin/employees', methods=['GET', 'POST'])
@admin_required
def admin_employees():
    import uuid
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        service_ids = request.form.getlist('service_ids')
        availability = request.form.get('availability')
        employee_tag = str(uuid.uuid4())[:8].upper() # Generate 8-char tag
        
        cursor.execute("""
            INSERT INTO employees (name, specialization, employee_tag, availability) 
            VALUES (%s, %s, %s, %s)
        """, (name, specialization, employee_tag, availability))
        employee_id = cursor.lastrowid
        
        for sid in service_ids:
            cursor.execute("INSERT INTO employee_services (employee_id, service_id) VALUES (%s, %s)", (employee_id, sid))
            
        conn.commit()
        flash(f'Employee added successfully. Tag: {employee_tag}', 'success')
        
    cursor.execute("""
        SELECT e.*, GROUP_CONCAT(s.service_name SEPARATOR ', ') as service_names 
        FROM employees e 
        LEFT JOIN employee_services es ON e.id = es.employee_id
        LEFT JOIN services s ON es.service_id = s.id
        GROUP BY e.id
    """)
    employees = cursor.fetchall()
    
    cursor.execute("SELECT employee_id, service_id FROM employee_services")
    es_records = cursor.fetchall()
    
    for emp in employees:
        emp['service_ids'] = [r['service_id'] for r in es_records if r['employee_id'] == emp['id']]
    
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_employees.html', employees=employees, services=services)

@app.route('/admin/employee/delete/<int:id>')
@admin_required
def delete_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Employee deleted successfully.', 'success')
    return redirect(url_for('admin_employees'))

@app.route('/admin/employee/edit/<int:id>', methods=['POST'])
@admin_required
def edit_employee(id):
    name = request.form.get('name')
    service_ids = request.form.getlist('service_ids')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET name = %s WHERE id = %s", (name, id))
    
    cursor.execute("DELETE FROM employee_services WHERE employee_id = %s", (id,))
    for sid in service_ids:
        cursor.execute("INSERT INTO employee_services (employee_id, service_id) VALUES (%s, %s)", (id, sid))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Employee updated successfully.', 'success')
    return redirect(url_for('admin_employees'))

@app.route('/doctor/dashboard')
@doctor_required
def doctor_dashboard():
    employee_id = session.get('employee_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT a.*, s.service_name
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        WHERE a.employee_id = %s
        ORDER BY a.date, a.time
    """, (employee_id,))
    appointments = cursor.fetchall()
    
    from datetime import datetime
    for appt in appointments:
        t_str = str(appt['time'])
        end_t_str = str(appt['end_time'])
        if len(t_str.split(':')) == 2: t_str += ':00'
        if len(end_t_str.split(':')) == 2: end_t_str += ':00'
        try:
            time_obj = datetime.strptime(t_str, '%H:%M:%S')
            end_time_obj = datetime.strptime(end_t_str, '%H:%M:%S')
            appt['display_time'] = time_obj.strftime('%I:%M %p') + ' - ' + end_time_obj.strftime('%I:%M %p')
        except ValueError:
            appt['display_time'] = t_str + ' - ' + end_t_str
    
    cursor.close()
    conn.close()
    return render_template('doctor_dashboard.html', appointments=appointments)

@app.route('/doctor/appointment/<int:id>/<action>')
@doctor_required
def doctor_appointment_action(id, action):
    if action not in ['approve', 'cancel']:
        return redirect(url_for('doctor_dashboard'))
        
    status_map = {'approve': 'Approved', 'cancel': 'Cancelled'}
    new_status = status_map[action]
    
    employee_id = session.get('employee_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure this appointment belongs to this doctor
    cursor.execute("UPDATE appointments SET status = %s WHERE id = %s AND employee_id = %s", 
                   (new_status, id, employee_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f'Appointment {new_status} successfully.', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/profile', methods=['GET', 'POST'])
@doctor_required
def doctor_profile():
    employee_id = session.get('employee_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            name = request.form.get('name')
            cursor.execute("UPDATE employees SET name = %s WHERE id = %s", (name, employee_id))
            conn.commit()
            session['name'] = name # Update session name
            flash('Profile updated successfully.', 'success')
        elif action == 'add_slot':
            day_of_week = request.form.get('day_of_week')
            time = request.form.get('time')
            end_time = request.form.get('end_time', '00:00:00')
            try:
                cursor.execute("INSERT INTO employee_schedules (employee_id, day_of_week, time, end_time) VALUES (%s, %s, %s, %s)",
                               (employee_id, day_of_week, time, end_time))
                conn.commit()
                flash('Schedule added successfully.', 'success')
            except mysql.connector.Error as err:
                flash('Error adding schedule. You may have already added this time for this day.', 'danger')
        elif action == 'add_service':
            service_id = request.form.get('service_id')
            if service_id:
                try:
                    cursor.execute("INSERT INTO employee_services (employee_id, service_id) VALUES (%s, %s)", (employee_id, service_id))
                    conn.commit()
                    flash('Service added successfully.', 'success')
                except mysql.connector.Error:
                    flash('You are already assigned to this service.', 'warning')
        elif action == 'remove_service':
            service_id = request.form.get('service_id')
            if service_id:
                cursor.execute("DELETE FROM employee_services WHERE employee_id = %s AND service_id = %s", (employee_id, service_id))
                conn.commit()
                flash('Service removed successfully.', 'success')
                
    cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    employee = cursor.fetchone()
    
    # Fetch assigned services
    cursor.execute("""
        SELECT s.* FROM services s
        JOIN employee_services es ON s.id = es.service_id
        WHERE es.employee_id = %s
    """, (employee_id,))
    assigned_services = cursor.fetchall()
    
    # Fetch all other services
    cursor.execute("""
        SELECT s.* FROM services s
        WHERE s.id NOT IN (
            SELECT service_id FROM employee_services WHERE employee_id = %s
        )
    """, (employee_id,))
    available_services = cursor.fetchall()
    
    cursor.execute("SELECT * FROM employee_schedules WHERE employee_id = %s ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), time", (employee_id,))
    schedules = cursor.fetchall()
    
    from datetime import datetime
    for sched in schedules:
        t_str = str(sched['time'])
        end_t_str = str(sched['end_time'])
        if len(t_str.split(':')) == 2: t_str += ':00'
        if len(end_t_str.split(':')) == 2: end_t_str += ':00'
        try:
            time_obj = datetime.strptime(t_str, '%H:%M:%S')
            end_time_obj = datetime.strptime(end_t_str, '%H:%M:%S')
            sched['display_time'] = time_obj.strftime('%I:%M %p') + ' - ' + end_time_obj.strftime('%I:%M %p')
        except ValueError:
            sched['display_time'] = t_str + ' - ' + end_t_str
    
    cursor.close()
    conn.close()
    
    return render_template('doctor_profile.html', employee=employee, schedules=schedules, assigned_services=assigned_services, available_services=available_services)

@app.route('/doctor/schedule/delete/<int:id>')
@doctor_required
def delete_schedule(id):
    employee_id = session.get('employee_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employee_schedules WHERE id = %s AND employee_id = %s", 
                   (id, employee_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Schedule deleted successfully.', 'success')
    return redirect(url_for('doctor_profile'))

@app.route('/api/appointments')
@login_required
def api_appointments():
    role = session.get('role')
    if role not in ['admin', 'doctor']:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if role == 'admin':
        cursor.execute("""
            SELECT a.patient_name, a.date, a.time, a.end_time, a.status, s.service_name, e.name as doctor_name 
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN employees e ON a.employee_id = e.id
            WHERE a.status != 'Cancelled'
        """)
    else:
        employee_id = session.get('employee_id')
        cursor.execute("""
            SELECT a.patient_name, a.date, a.time, a.end_time, a.status, s.service_name, e.name as doctor_name 
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN employees e ON a.employee_id = e.id
            WHERE a.status != 'Cancelled' AND a.employee_id = %s
        """, (employee_id,))
        
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    
    events = []
    for appt in appointments:
        date_str = appt['date'].strftime('%Y-%m-%d')
        # Pad with 0 to ensure HH:MM:SS format
        start_time = str(appt['time']).zfill(8)
        end_time = str(appt['end_time']).zfill(8)
        
        color = '#198754' if appt['status'] == 'Approved' else '#ffc107'
        text_color = '#ffffff' if appt['status'] == 'Approved' else '#000000'
        
        title = f"{appt['patient_name']} - {appt['service_name']} (Dr. {appt['doctor_name']})"
        
        events.append({
            'title': title,
            'start': f"{date_str}T{start_time}",
            'end': f"{date_str}T{end_time}",
            'backgroundColor': color,
            'borderColor': color,
            'textColor': text_color,
            'extendedProps': {
                'patient_name': appt['patient_name'],
                'service_name': appt['service_name'],
                'doctor_name': appt['doctor_name'],
                'status': appt['status'],
                'time_range': f"{start_time} - {end_time}",
                'date': date_str
            }
        })
        
    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
