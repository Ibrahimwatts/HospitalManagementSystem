from flask import Flask, render_template, request, redirect, url_for, flash, session
from db_config import create_connection, close_connection
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user  # Add this line

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For flash messages

# Home route
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    role = session.get('role')

    return render_template('dashboard.html', role=role)

# Route to view and manage patients
@app.route('/patients')
def patients():
    if 'username' not in session:
        return redirect(url_for('login'))

    connection = create_connection()
    if connection is None:
        flash("Failed to connect to the database.")
        return redirect(url_for('dashboard'))

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM patients")
        patients_list = cursor.fetchall()
    except Exception as e:
        flash(f"An error occurred: {e}")
        patients_list = []
    finally:
        close_connection(connection)

    return render_template('patient_management.html', patients=patients_list, role=session.get('role'))

# Add new patient
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone_number = request.form['phone_number']
        email = request.form['email']
        medical_history = request.form['medical_history']

        connection = create_connection()
        if connection is None:
            flash("Failed to connect to the database.")
            return redirect(url_for('add_patient'))

        cursor = connection.cursor()
        try:
            cursor.execute("""INSERT INTO patients 
                (first_name, last_name, age, gender, address, phone_number, email, medical_history)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (first_name, last_name, age, gender, address, phone_number, email, medical_history))
            connection.commit()
            flash("Patient added successfully!")
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            close_connection(connection)
        
        return redirect(url_for('patients'))

    return render_template('add_patient.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Get the role from the form

        connection = create_connection()
        if connection is None:
            flash("Failed to connect to the database.")
            return redirect(url_for('register'))

        cursor = connection.cursor()
        try:
            hashed_password = generate_password_hash(password)  # Hash the password
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                           (username, hashed_password, role))
            connection.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            close_connection(connection)

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Establish connection with the database
        connection = create_connection()
        if connection is None:
            flash("Failed to connect to the database.")
            return redirect(url_for('login'))

        cursor = connection.cursor(dictionary=True)
        try:
            # Fetch the user by username
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user:
                # Check if the password matches
                if check_password_hash(user['password'], password):
                    # Store session details
                    session['username'] = username
                    session['role'] = user['role']  # Store the user's role (e.g., 'admin', 'user')
                    
                    flash("Login successful!")
                    return redirect(url_for('dashboard'))
                else:
                    flash("Invalid username or password.")
            else:
                flash("User not found.")
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            close_connection(connection)
    
    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

# Route for admins to edit/delete patients
@app.route('/manage_patients')
def manage_patients():
    if 'username' not in session or session['role'] != 'admin':
        flash("You are not authorized to view this page.")
        return redirect(url_for('dashboard'))
    
    connection = create_connection()
    if connection is None:
        flash("Failed to connect to the database.")
        return redirect(url_for('dashboard'))

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM patients")
        patients_list = cursor.fetchall()
    except Exception as e:
        flash(f"An error occurred: {e}")
        patients_list = []
    finally:
        close_connection(connection)
    
    return render_template('patient_management.html', patients=patients_list)

# Edit patient route (admin)
@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    if 'username' not in session or session.get('role') != 'admin':
        flash("Unauthorized access")
        return redirect(url_for('login'))

    connection = create_connection()
    if connection is None:
        flash("Failed to connect to the database.")
        return redirect(url_for('dashboard'))

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        # Fetch updated details from the form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        phone_number = request.form['phone_number']
        email = request.form['email']
        medical_history = request.form['medical_history']

        try:
            cursor.execute("""
                UPDATE patients 
                SET first_name = %s, last_name = %s, age = %s, gender = %s, address = %s, phone_number = %s, email = %s, medical_history = %s 
                WHERE id = %s
            """, (first_name, last_name, age, gender, address, phone_number, email, medical_history, id))
            connection.commit()
            flash("Patient updated successfully.")
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            close_connection(connection)

        return redirect(url_for('patients'))

    # Fetch current patient details
    try:
        cursor.execute("SELECT * FROM patients WHERE id = %s", (id,))
        patient = cursor.fetchone()
    except Exception as e:
        flash(f"An error occurred: {e}")
        return redirect(url_for('patients'))
    finally:
        close_connection(connection)

    return render_template('edit_patient.html', patient=patient)

# Delete patient route (admin)
@app.route('/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    if 'username' not in session or session['role'] != 'admin':
        flash("You are not authorized to perform this action.")
        return redirect(url_for('dashboard'))

    connection = create_connection()
    if connection is None:
        flash("Failed to connect to the database.")
        return redirect(url_for('dashboard'))

    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        connection.commit()
        flash("Patient deleted successfully.")
    except Exception as e:
        flash(f"An error occurred: {e}")
    finally:
        close_connection(connection)

    return redirect(url_for('manage_patients'))

# View Bills and Balances
@app.route('/view_bills')
def view_bills():
    # Check if the user is logged in
    if 'username' not in session:
        flash("Please log in to view bills.")
        return redirect(url_for('login'))

    # Establish connection with the database
    connection = create_connection()
    if connection is None:
        flash("Failed to connect to the database.")
        return redirect(url_for('dashboard'))

    cursor = connection.cursor(dictionary=True)
    try:
        # Fetch all bills from the 'bills' table
        cursor.execute("SELECT * FROM bills")
        bills = cursor.fetchall()
    except Exception as e:
        flash(f"An error occurred: {e}")
        bills = []  # Empty list in case of error
    finally:
        close_connection(connection)

    # Check if the logged-in user is an admin
    user_role = session.get('role', 'user')  # Default to 'user' if no role is set

    # Render the 'view_bills.html' template with the fetched bills data and the user role
    return render_template('view_bills.html', bills=bills, user_role=user_role)



@app.route('/delete_bill/<int:patient_id>', methods=['POST'])
def delete_bill(patient_id):
    if 'username' not in session or session.get('role') != 'admin':
        flash("Unauthorized access")
        return redirect(url_for('login'))
    
    # Database connection
    connection = create_connection()
    if connection is None:
        flash("Failed to connect to the database.")
        return redirect(url_for('dashboard'))

    cursor = connection.cursor()
    try:
        # Delete the bill with the corresponding patient_id
        cursor.execute("DELETE FROM bills WHERE patient_id = %s", (patient_id,))
        connection.commit()
        flash("Bill deleted successfully.")
    except Exception as e:
        flash(f"An error occurred: {e}")
    finally:
        close_connection(connection)
    
    return redirect(url_for('view_bills'))



# Update Bills and Balances (Admin only)
@app.route('/update_bills', methods=['GET', 'POST'])
def update_bills():
    # Check if the user is logged in and is an admin
    if 'username' not in session or session.get('role') != 'admin':
        flash("Unauthorized access")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Fetch form data
        patient_id = request.form.get('patient_id')
        total_amount = request.form.get('total_amount')
        balance = request.form.get('balance')
        status = request.form.get('status')

        # Ensure all fields are filled
        if not patient_id or not total_amount or not balance or not status:
            flash("All fields are required.")
            return redirect(url_for('update_bills'))

        # Convert form data to appropriate types (e.g., patient_id to int, amounts to decimals)
        try:
            patient_id = int(patient_id)
            total_amount = float(total_amount)
            balance = float(balance)
        except ValueError:
            flash("Invalid input. Please ensure numeric values for patient ID, total amount, and balance.")
            return redirect(url_for('update_bills'))

        # Establish connection with the database
        connection = create_connection()
        if connection is None:
            flash("Failed to connect to the database.")
            return redirect(url_for('dashboard'))

        cursor = connection.cursor()

        try:
            # Check if a bill already exists for the given patient_id
            cursor.execute("SELECT * FROM bills WHERE patient_id = %s", (patient_id,))
            existing_bill = cursor.fetchone()

            if existing_bill:
                # Update the bill if it already exists
                update_query = """
                    UPDATE bills 
                    SET total_amount = %s, balance = %s, status = %s
                    WHERE patient_id = %s
                """
                cursor.execute(update_query, (total_amount, balance, status, patient_id))
                flash("Bill updated successfully.")
            else:
                # Insert a new bill if none exists
                insert_query = """
                    INSERT INTO bills (patient_id, total_amount, balance, status)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (patient_id, total_amount, balance, status))
                flash("New bill added successfully.")

            # Commit the changes to the database
            connection.commit()

        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            close_connection(connection)

    return render_template('update_bills.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
