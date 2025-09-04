from flask import Flask, render_template, request, abort, redirect, url_for, session, jsonify, flash
from flask_mysqldb import MySQL
from flask import send_from_directory
from gpt2 import generate_response
import MySQLdb.cursors
import re
import os
import uuid
from waitress import serve  # Import waitress
from datetime import datetime
import logging

app = Flask(__name__)

app.secret_key = 'abcd2123445'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'library-system'

mysql = MySQL(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.route('/reviews/', methods=['GET', 'POST'])
def reviews():
    if request.method == 'POST':
        if 'id' not in session:
            flash("Please login to submit a review.", "error")
            return redirect(url_for('login'))

        try:
            user_id = session['id']
            book_id = request.form.get('book_id')
            review = request.form.get('review', '').strip()
            rating = request.form.get('rating')

            # Validate inputs
            if not all([book_id, review, rating]):
                flash("All fields are required.", "error")
                return redirect(url_for('reviews'))

            try:
                rating = int(rating)
                if not 1 <= rating <= 5:
                    raise ValueError
            except ValueError:
                flash("Invalid rating value.", "error")
                return redirect(url_for('reviews'))

            # Check if user has already reviewed this book
            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT id FROM reviews WHERE user_id = %s AND book_id = %s",
                (user_id, book_id)
            )
            existing_review = cursor.fetchone()

            if existing_review:
                # Update existing review
                cursor.execute(
                    """UPDATE reviews 
                       SET review = %s, rating = %s, updated_on = NOW()
                       WHERE user_id = %s AND book_id = %s""",
                    (review, rating, user_id, book_id)
                )
            else:
                # Insert new review
                cursor.execute(
                    """INSERT INTO reviews 
                       (user_id, book_id, review, rating, created_on)
                       VALUES (%s, %s, %s, %s, NOW())""",
                    (user_id, book_id, review, rating)
                )

            mysql.connection.commit()
            flash("Review submitted successfully!", "success")
            return redirect(url_for('reviews'))

        except Exception as e:
            mysql.connection.rollback()
            app.logger.error(f"Error processing review: {str(e)}")
            flash("An error occurred while processing your review.", "error")
            return redirect(url_for('reviews'))

        finally:
            cursor.close()

    # GET request handling
    try:
        cursor = mysql.connection.cursor()
        
        # Fetch books
        cursor.execute(
            "SELECT bookid, name FROM book ORDER BY name"
        )
        books = cursor.fetchall()

        # Fetch reviews with user details and book information
        cursor.execute("""
            SELECT 
                r.review,
                r.rating,
                r.created_on,
                u.first_name,
                b.name as book_name
            FROM reviews r
            JOIN user u ON r.user_id = u.id
            JOIN book b ON r.book_id = b.bookid
            ORDER BY r.created_on DESC
        """)
        reviews = cursor.fetchall()

        return render_template('reviews.html', books=books, reviews=reviews)

    except Exception as e:
        app.logger.error(f"Error fetching review data: {str(e)}")
        flash("Unable to load reviews at this time.", "error")
        return render_template('reviews.html', books=[], reviews=[])

    finally:
        if cursor:
            cursor.close()

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Get JSON data from the request
        data = request.get_json()

        # Log the incoming data for debugging
        print(f"Incoming data: {data}")

        # Extract the user message from the incoming data
        user_message = data.get('message')

        # Check if the message is missing
        if not user_message:
            return jsonify({"error": "No message provided!"}), 400

        # Log the received message for debugging
        print(f"User Message: {user_message}")

        # Pass the `mysql` object to `generate_response`
        response = generate_response(user_message, mysql)

        # Log the generated response for debugging
        print(f"Generated Response: {response}")

        # Check if the response is None or empty
        if not response:
            return jsonify({"error": "Failed to generate a response"}), 500

        # If the response contains HTML (e.g., a download link), return it directly
        if '<a href' in response:  # Check if the response contains HTML
            return jsonify({"response": response})

        # Otherwise, return the response as JSON
        return jsonify({"response": response})

    except Exception as e:
        # Log the error and return a 500 status
        print(f"Error in chat route: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/search', methods=['POST'])
def search_books():
    print("Search route accessed")  # Debugging line

    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "Query parameter is missing"}), 400

    # Create a cursor to interact with the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Execute the query to join book with author and publisher
        cursor.execute("""
            SELECT book.bookid, book.name, book.isbn, book.no_of_copy, book.status, 
                   author.name, publisher.name
            FROM book
            JOIN author ON book.authorid = author.authorid
            JOIN publisher ON book.publisherid = publisher.publisherid
            WHERE book.name LIKE %s
        """, ('%' + query + '%',))

        # Fetch the results
        results = cursor.fetchall()

        # Debugging line: print the results to see what is returned
        print("Results from DB:", results)

        # If no results, return a specific message
        if not results:
            return jsonify({"message": "No books found matching the query"}), 404

    except Exception as e:
        # Log the error
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        cursor.close()

    return jsonify(results)  # Return the results here


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']  # Change to email instead of username
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password))  # Query using email
        user = cursor.fetchone()
        
        if user:
            # Set session variables
            session['loggedin'] = True
            session['id'] = user['id']
            session['email'] = user['email']  # Store email in session instead of username
            session['role'] = user['role']  # Assuming the 'role' column exists in your user table
            session['name'] = user['first_name']
            print(session)  # To verify what's being stored

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('dashboard'))  # Redirect to admin dashboard
            else:
                return redirect(url_for('library'))  # Redirect to user library page

        else:
            msg = 'Incorrect email or password!'  # Updated message
            return render_template('login.html', msg=msg)

    return render_template('login.html')

@app.route("/query", methods=['GET', 'POST'])
def query():
    if 'loggedin' in session:
        if request.method == 'POST':
            # Get the data from the form
            book_request = request.form.get('book_request')  # Using .get() to prevent errors
            description = request.form.get('description')  # Using .get() for description
            
            # Check if both fields are filled
            if not book_request or not description:
                # If any of the fields is empty, flash a message
                flash("Both fields are required!", "error")
                return redirect(url_for('query'))  # Redirect to the query page again
            
            try:
                # Save the query to the database
                cursor = mysql.connection.cursor()
                cursor.execute("INSERT INTO queries (book_request, description) VALUES (%s, %s)", 
                               (book_request, description))
                mysql.connection.commit()
                cursor.close()
                
                # Flash a success message
                flash("Query submitted successfully!", "success")
                return redirect(url_for('query'))  # Redirect to the query page after saving

            except MySQLdb.Error as e:
                # Handle database errors
                flash(f"An error occurred: {e}", "error")
                return redirect(url_for('query'))  # Redirect to the query page on error

        else:
            # If the method is GET, fetch the queries from the database and display them
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("SELECT * FROM queries")  # Get all queries
                queries = cursor.fetchall()  # Fetch all rows
                cursor.close()
            except MySQLdb.Error as e:
                # Handle database errors when fetching queries
                flash(f"An error occurred while fetching queries: {e}", "error")
                queries = []  # In case of an error, pass an empty list

            # Render the template with existing queries
            return render_template("query.html", queries=queries)  # Pass queries to the template
            
    else:
        # If the user is not logged in, redirect them to the login page
        flash("You must be logged in to view and submit queries.", "warning")
        return redirect(url_for('login'))

@app.route("/library")
def library():
    if 'loggedin' in session:
        # Show the library page for both users and admins
        return render_template("library.html")
    else:
        # If the user is not logged in, redirect them to the login page
        return redirect(url_for('login'))

    
@app.route("/dashboard")
def dashboard():
    if 'loggedin' in session and session['role'] == 'admin':
        # Your admin dashboard logic
        return render_template('dashboard.html')  # Ensure the .html extension is included
    return redirect(url_for('home'))

@app.route("/api/dashboard-stats")
def get_dashboard_stats():
    if 'loggedin' in session and session['role'] == 'admin':
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Get total books
            cursor.execute("SELECT COUNT(*) as total FROM book")
            total_books = cursor.fetchone()['total']
            
            # Get available books (not issued)
            cursor.execute("SELECT COUNT(*) as available FROM book WHERE bookid NOT IN (SELECT bookid FROM issued_book WHERE status = 'issued')")
            available_books = cursor.fetchone()['available']
            
            # Get currently issued books
            cursor.execute("SELECT COUNT(*) as issued FROM issued_book WHERE status = 'issued'")
            issued_books = cursor.fetchone()['issued']
            
            # Get returned books
            cursor.execute("SELECT COUNT(*) as returned FROM issued_book WHERE status = 'returned'")
            returned_books = cursor.fetchone()['returned']
            
            cursor.close()
            mysql.connection.commit()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_books': total_books,
                    'available_books': available_books,
                    'issued_books': issued_books,
                    'returned_books': returned_books
                }
            })
            
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return jsonify({'success': False, 'error': 'Database error occurred'})
            
    return jsonify({'success': False, 'error': 'Unauthorized access'})

    
@app.route("/users", methods =['GET', 'POST'])
def users():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user')
        users = cursor.fetchall()    
        return render_template("users.html", users = users)
    return redirect(url_for('home'))

@app.route("/save_user", methods =['GET', 'POST'])
def save_user():
    msg = ''    
    if 'loggedin' in session and session['role'] == 'admin':        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST' and 'role' in request.form and 'first_name' in request.form and 'last_name' in request.form and 'email' in request.form :
            
            first_name = request.form['first_name']  
            last_name = request.form['last_name'] 
            email = request.form['email']            
            role = request.form['role']             
            action = request.form['action']
            
            if action == 'updateUser':
                userId = request.form['userid']                 
                cursor.execute('UPDATE user SET first_name= %s, last_name= %s, email= %s, role= %s WHERE id = %s', (first_name, last_name, email, role, (userId, ), ))
                mysql.connection.commit()   
            else:
                password = request.form['password'] 
                cursor.execute('INSERT INTO user (`first_name`, `last_name`, `email`, `password`, `role`) VALUES (%s, %s, %s, %s, %s)', (first_name, last_name, email, password, role))
                mysql.connection.commit()   

            return redirect(url_for('users'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form !'        
        return redirect(url_for('users'))      
    return redirect(url_for('home'))

@app.route("/edit_user", methods =['GET', 'POST'])
def edit_user():
    msg = ''    
    if 'loggedin' in session and session['role'] == 'admin':
        editUserId = request.args.get('userid')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE id = % s', (editUserId, ))
        users = cursor.fetchall()         

        return render_template("edit_user.html", users = users)
    return redirect(url_for('home'))

@app.route("/view_user", methods=['GET', 'POST'])
def view_user():
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch 'userid' from URL if provided, else default to logged-in user's ID
        viewUserId = request.args.get('userid')  # Fetch 'userid' from URL
        
        # If no 'userid' is passed, default to the logged-in user's ID
        if not viewUserId:
            viewUserId = session['id']
        
        try:
            # Fetch user details from the database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user WHERE id = %s', (viewUserId,))  # Use the correct user ID
            user = cursor.fetchone()
            cursor.close()

            # Handle case where no user is found
            if not user:
                return redirect(url_for('error_page', message="User not found."))  # Redirect to a custom error page
            
            # Print user for debugging (remove this in production)
            print(user)  
            
            # Return the user details to the template
            return render_template("view_user.html", user=user)

        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    else:
        # Redirect to login if not logged in
        return redirect(url_for('login'))
     
@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    message = ''
    
    if request.method == 'POST':
        email = request.form['email']
        
        # Check if the email exists in the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            # Generate a reset token for the password reset link
            reset_token = str(uuid.uuid4())  # Generate a unique token
            
            # Update the user record with the reset token (for simplicity, storing in the user table here)
            cursor.execute('UPDATE user SET reset_token = %s WHERE email = %s', (reset_token, email))
            mysql.connection.commit()
            
            # Here you would normally send the reset link to the user's email (this is just for demo)
            reset_link = url_for('reset_password', token=reset_token, _external=True)
            
            # You can integrate email service to send the reset link via email, e.g., using Flask-Mail.
            # For simplicity, we'll just show the reset link here
            message = f'Password reset link: {reset_link}'

        else:
            message = 'Email address not found! Please check your email.'
    
    return render_template("forgot_password.html", message=message)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    message = ''
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            message = "Passwords do not match!"
        else:
            # Find user by reset token
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user WHERE reset_token = %s', (token,))
            user = cursor.fetchone()
            
            print(f"User found: {user}")  # Debug print to check if user is fetched
            
            if user:
                # Store the password as plain text (no hashing)
                cursor.execute('UPDATE user SET password = %s, reset_token = NULL WHERE reset_token = %s', (new_password, token))
                mysql.connection.commit()
                
                print(f"Rows affected: {cursor.rowcount}")  # Check if rows were updated
                
                if cursor.rowcount > 0:
                    message = "Password successfully updated! You can now log in."
                    return redirect(url_for('login'))  # Redirect to login page
                else:
                    message = "No rows were updated. There might be an issue with the reset token."
            else:
                message = "Invalid or expired reset token."
    
    return render_template("reset_password.html", message=message, token=token)

    
@app.route("/delete_user", methods =['GET'])
def delete_user():
    if 'loggedin' in session:
        deleteUserId = request.args.get('userid')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM user WHERE userid = % s', (deleteUserId, ))
        mysql.connection.commit()   
        return redirect(url_for('users'))
    return redirect(url_for('login'))
  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))
  
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        
        # Validate the input fields
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            # If validation passes, insert the user into the database
            # Assuming 'first_name' and 'last_name' need to be collected from the form as well
            first_name, last_name = userName.split(' ')[0], ' '.join(userName.split(' ')[1:])
            cursor.execute('INSERT INTO user (first_name, last_name, email, password, role) VALUES (%s, %s, %s, %s, %s)', 
                           (first_name, last_name, email, password, 'user'))
            mysql.connection.commit()
            message = 'You have successfully registered!'

    elif request.method == 'POST':
        message = 'Please fill out the form!'

    return render_template('register.html', message=message)

@app.route("/books", methods=['GET', 'POST'])
def books():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Fetch books with their details, including the picture
        cursor.execute(''' 
            SELECT b.bookid, b.name, b.authorid, b.categoryid, b.status, b.isbn, b.added_on, b.updated_on, 
                   a.name as author_name, c.name as category_name, p.name as publisher_name, b.pdf_path, b.picture
            FROM book b
            LEFT JOIN author a ON b.authorid = a.authorid
            LEFT JOIN category c ON b.categoryid = c.categoryid
            LEFT JOIN publisher p ON b.publisherid = p.publisherid
        ''')
        books = cursor.fetchall()  # Fetch all books with the necessary details
        
        return render_template("books.html", books=books)
    return redirect(url_for('home'))

@app.route("/save_book", methods=['GET', 'POST'])
def save_book():
    if 'loggedin' in session and session['role'] == 'admin':
        bookid = request.args.get('bookid')  # Fetch bookid from the URL query parameter
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if request.method == 'POST' and 'authorid' in request.form and 'name' in request.form and 'categoryid' in request.form:
            name = request.form['name']
            authorid = request.form['authorid']
            categoryid = request.form['categoryid']
            status = request.form['status']
            isbn = request.form['isbn']
            publisherid = request.form['publisherid']

            # Handle the PDF upload
            pdf_file = request.files.get('pdf')
            pdf_file_path = None
            if pdf_file:
                pdf_file_path = os.path.join('static', 'books', pdf_file.filename)
                pdf_file.save(pdf_file_path)

            # Handle the picture upload
            picture_file = request.files.get('picture')
            picture_file_path = None
            if picture_file:
                picture_file_path = os.path.join('static', 'books', picture_file.filename)
                picture_file.save(picture_file_path)

            action = request.form.get('action', 'addBook')

            if action == 'updateBook' and bookid:  # Update only if action is updateBook and bookid is provided
                cursor.execute(''' 
                    UPDATE book 
                    SET name = %s, authorid = %s, categoryid = %s, status = %s, isbn = %s, pdf_path = %s, picture = %s, publisherid = %s, updated_on = NOW()
                    WHERE bookid = %s
                ''', (name, authorid, categoryid, status, isbn, pdf_file_path, picture_file_path, publisherid, bookid))
                mysql.connection.commit()
            else:
                cursor.execute(''' 
                    INSERT INTO book (name, authorid, categoryid, status, isbn, pdf_path, picture, publisherid, added_on, updated_on)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ''', (name, authorid, categoryid, status, isbn, pdf_file_path, picture_file_path, publisherid))
                mysql.connection.commit()

            return redirect(url_for('books'))

        elif request.method == 'POST':
            msg = 'Please fill out the form!'

        return redirect(url_for('books'))
    return redirect(url_for('home'))

@app.route("/edit_book", methods=['GET', 'POST'])
def edit_book():
    if 'loggedin' in session and session['role'] == 'admin':
        bookid = request.args.get('bookid')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if bookid:
            cursor.execute('''
                SELECT b.bookid, b.name, b.authorid, b.categoryid, b.status, b.isbn, 
                       b.pdf_path, b.picture, b.added_on, b.updated_on, b.no_of_copy,
                       a.name as author_name, c.name as category_name, 
                       p.name as publisher_name, b.publisherid
                FROM book b
                LEFT JOIN author a ON b.authorid = a.authorid
                LEFT JOIN category c ON b.categoryid = c.categoryid
                LEFT JOIN publisher p ON b.publisherid = p.publisherid
                WHERE b.bookid = %s
            ''', (bookid,))
            books = cursor.fetchone()
        else:
            books = {}
        
        cursor.execute('SELECT authorid, name FROM author')
        authors = cursor.fetchall()
        
        cursor.execute('SELECT categoryid, name FROM category')
        categories = cursor.fetchall()
        
        cursor.execute('SELECT publisherid, name FROM publisher')
        publishers = cursor.fetchall()
        
        if request.method == 'POST':
            name = request.form['name']
            authorid = request.form.get('authorid')
            categoryid = request.form.get('categoryid')
            status = request.form['status']
            isbn = request.form['isbn']
            publisherid = request.form.get('publisherid')
            no_of_copy = request.form['no_of_copy']
            
            # Handle PDF file
            pdf_file = request.files.get('pdf')
            pdf_path = books.get('pdf_path') if books else None  # Keep existing if no new file
            if pdf_file and pdf_file.filename:
                # Store only filename
                pdf_path = pdf_file.filename
                # Save file with full path
                pdf_file.save(os.path.join('static', 'books', pdf_file.filename))
            
            # Handle picture file
            picture_file = request.files.get('picture')
            picture_path = books.get('picture') if books else None  # Keep existing if no new file
            if picture_file and picture_file.filename:
                # Store only filename
                picture_path = picture_file.filename
                # Save file with full path
                picture_file.save(os.path.join('static', 'books', picture_file.filename))
            
            # Handle new author if provided
            if request.form.get('new_author'):
                cursor.execute('INSERT INTO author (name) VALUES (%s)', (request.form['new_author'],))
                mysql.connection.commit()
                authorid = cursor.lastrowid
                
            # Handle new category if provided
            if request.form.get('new_category'):
                cursor.execute('INSERT INTO category (name) VALUES (%s)', (request.form['new_category'],))
                mysql.connection.commit()
                categoryid = cursor.lastrowid
                
            # Handle new publisher if provided
            if request.form.get('new_publisher'):
                cursor.execute('INSERT INTO publisher (name) VALUES (%s)', (request.form['new_publisher'],))
                mysql.connection.commit()
                publisherid = cursor.lastrowid
            
            if bookid:
                cursor.execute('''
                    UPDATE book
                    SET name = %s, authorid = %s, categoryid = %s, status = %s, 
                        isbn = %s, pdf_path = %s, picture = %s, publisherid = %s, 
                        no_of_copy = %s, updated_on = NOW()
                    WHERE bookid = %s
                ''', (name, authorid, categoryid, status, isbn, pdf_path, 
                      picture_path, publisherid, no_of_copy, bookid))
            else:
                cursor.execute('''
                    INSERT INTO book (name, authorid, categoryid, status, isbn, 
                                    pdf_path, picture, publisherid, no_of_copy, added_on)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ''', (name, authorid, categoryid, status, isbn, pdf_path, 
                      picture_path, publisherid, no_of_copy))
            
            mysql.connection.commit()
            return redirect(url_for('books'))
        
        return render_template("edit_books.html", books=books, authors=authors, 
                             categories=categories, publishers=publishers)
    
    return redirect(url_for('home'))


@app.route("/delete_book", methods=['GET'])
def delete_book():
    if 'loggedin' in session and session['role'] == 'admin':
        bookid = request.args.get('bookid')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM book WHERE bookid = %s', (bookid,))
        mysql.connection.commit()
        return redirect(url_for('books'))
    return redirect(url_for('home'))


@app.route('/download_pdf/<identifier>')
def download_pdf(identifier):
    cur = mysql.connection.cursor()
    
    # Try to fetch by bookid first
    cur.execute("SELECT pdf_path FROM book WHERE bookid = %s", (identifier,))
    result = cur.fetchone()
    
    if not result or not result[0]:
        # If not found, try searching by ISBN
        cur.execute("SELECT pdf_path FROM book WHERE isbn = %s", (identifier,))
        result = cur.fetchone()
    
    if not result or not result[0]:
        abort(404)  # Return 404 if file doesn't exist
    
    pdf_path = result[0].strip()
    return send_from_directory('static/books', pdf_path, as_attachment=True)


# Manage Issue Book (Admin Only)
@app.route("/list_issue_book", methods=['GET', 'POST'])
def list_issue_book():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT issued_book.issuebookid, issued_book.issue_date_time, issued_book.expected_return_date, issued_book.return_date_time, issued_book.status, book.name AS book_name, book.isbn, user.first_name, user.last_name FROM issued_book LEFT JOIN book ON book.bookid = issued_book.bookid LEFT JOIN user ON user.id = issued_book.userid")
        issue_books = cursor.fetchall()

        cursor.execute("SELECT bookid, name FROM book")
        books = cursor.fetchall()

        cursor.execute("SELECT id, first_name, last_name FROM user")
        users = cursor.fetchall()

        return render_template("issue_book.html", issue_books=issue_books, books=books, users=users)
    return redirect(url_for('home'))


@app.route("/save_issue_book", methods=['GET', 'POST'])
def save_issue_book():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT issued_book.issuebookid, issued_book.issue_date_time, issued_book.expected_return_date, issued_book.return_date_time, issued_book.status, book.name AS book_name, book.isbn, user.first_name, user.last_name FROM issued_book LEFT JOIN book ON book.bookid = issued_book.bookid LEFT JOIN user ON user.id = issued_book.userid")
        issue_books = cursor.fetchall()

        if request.method == 'POST' and 'book' in request.form and 'users' in request.form and 'expected_return_date' in request.form and 'return_date' in request.form and 'status' in request.form:
            bookId = request.form['book']
            userId = request.form['users']
            expected_return_date = request.form['expected_return_date']
            return_date = request.form['return_date']
            status = request.form['status']
            action = request.form['action']

            if action == 'updateIssueBook':
                issuebookid = request.form['issueBookId']
                cursor.execute('UPDATE issued_book SET bookid = %s, userid = %s, expected_return_date = %s, return_date_time = %s, status = %s WHERE issuebookid = %s', (bookId, userId, expected_return_date, return_date, status, issuebookid))
                mysql.connection.commit()
            else:
                cursor.execute('INSERT INTO issued_book (`bookid`, `userid`, `expected_return_date`, `return_date_time`, `status`) VALUES (%s, %s, %s, %s, %s)', (bookId, userId, expected_return_date, return_date, status))
                mysql.connection.commit()

            return redirect(url_for('list_issue_book'))
        return redirect(url_for('list_issue_book'))
    return redirect(url_for('home'))


@app.route("/edit_issue_book", methods=['GET', 'POST'])
def edit_issue_book():
    if 'loggedin' in session and session['role'] == 'admin':
        issuebookid = request.args.get('issuebookid')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT issued_book.issuebookid, issued_book.issue_date_time, issued_book.expected_return_date, issued_book.return_date_time, issued_book.bookid, issued_book.userid, issued_book.status, book.name AS book_name, book.isbn, user.first_name, user.last_name FROM issued_book LEFT JOIN book ON book.bookid = issued_book.bookid LEFT JOIN user ON user.id = issued_book.userid WHERE issued_book.issuebookid = %s', (issuebookid,))
        issue_books = cursor.fetchall()

        cursor.execute("SELECT bookid, name FROM book")
        books = cursor.fetchall()

        cursor.execute("SELECT id, first_name, last_name FROM user")
        users = cursor.fetchall()

        return render_template("edit_issue_book.html", issue_books=issue_books, books=books, users=users)
    return redirect(url_for('home'))


@app.route("/delete_issue_book", methods=['GET'])
def delete_issue_book():
    if 'loggedin' in session and session['role'] == 'admin':
        issuebookid = request.args.get('issuebookid')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM issued_book WHERE issuebookid = %s', (issuebookid,))
        mysql.connection.commit()
        return redirect(url_for('list_issue_book'))
    return redirect(url_for('home'))

# Manage Category   
@app.route("/category", methods=['GET', 'POST'])
def category():
    if 'loggedin' in session and session['role'] == 'admin':        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT categoryid, name, status FROM category")
        categories = cursor.fetchall()    
        return render_template("category.html", categories=categories, addCategoryForm=0)
    return redirect(url_for('home'))

@app.route("/saveCategory", methods=['GET', 'POST'])
def saveCategory():
    if 'loggedin' in session and session['role'] == 'admin':  
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST' and 'name' in request.form and 'status' in request.form:
            name = request.form['name'] 
            status = request.form['status']             
            action = request.form['action']             
            if action == 'updateCategory':
                categoryId = request.form['categoryid'] 
                cursor.execute('UPDATE category SET name = %s, status = %s WHERE categoryid = %s', (name, status, categoryId))
                mysql.connection.commit()        
            else: 
                cursor.execute('INSERT INTO category (`name`, `status`) VALUES (%s, %s)', (name, status))
                mysql.connection.commit()        
            return redirect(url_for('category'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form !'        
        return redirect(url_for('category'))
    return redirect(url_for('home'))
    
@app.route("/editCategory", methods=['GET', 'POST'])
def editCategory():
    if 'loggedin' in session and session['role'] == 'admin': 
        categoryid = request.args.get('categoryid') 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT categoryid, name, status FROM category WHERE categoryid = %s', (categoryid,))
        categories = cursor.fetchall() 
        return render_template("edit_category.html", categories=categories)
    return redirect(url_for('home'))

@app.route("/delete_category", methods=['GET'])
def delete_category():
    if 'loggedin' in session and session['role'] == 'admin':
        categoryid = request.args.get('categoryid') 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM category WHERE categoryid = %s', (categoryid,))
        mysql.connection.commit()   
        return redirect(url_for('category'))
    return redirect(url_for('home'))
# Manage Author   
@app.route("/author", methods=['GET', 'POST'])
def author():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT authorid, name, status FROM author")
        authors = cursor.fetchall()    
        return render_template("author.html", authors=authors)
    return redirect(url_for('home'))

@app.route("/saveAuthor", methods=['GET', 'POST'])
def saveAuthor():
    if 'loggedin' in session and session['role'] == 'admin':  
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST' and 'name' in request.form and 'status' in request.form:
            name = request.form['name'] 
            status = request.form['status']             
            action = request.form['action']             
            if action == 'updateAuthor':
                authorId = request.form['authorid'] 
                cursor.execute('UPDATE author SET name = %s, status = %s WHERE authorid = %s', (name, status, authorId))
                mysql.connection.commit()        
            else: 
                cursor.execute('INSERT INTO author (`name`, `status`) VALUES (%s, %s)', (name, status))
                mysql.connection.commit()        
            return redirect(url_for('author'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form !'        
        return redirect(url_for('author'))
    return redirect(url_for('home'))

@app.route("/editAuthor", methods=['GET', 'POST'])
def editAuthor():
    if 'loggedin' in session and session['role'] == 'admin': 
        authorid = request.args.get('authorid') 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT authorid, name, status FROM author WHERE authorid = %s', (authorid,))
        authors = cursor.fetchall() 
        return render_template("edit_author.html", authors=authors)
    return redirect(url_for('home'))  

@app.route("/delete_author", methods=['GET'])
def delete_author():
    if 'loggedin' in session and session['role'] == 'admin':
        authorid = request.args.get('authorid') 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM author WHERE authorid = %s', (authorid,))
        mysql.connection.commit()   
        return redirect(url_for('author'))
    return redirect(url_for('home'))

# Manage Publishers   
@app.route("/publisher", methods=['GET', 'POST'])
def publisher():
    if 'loggedin' in session and session['role'] == 'admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT publisherid, name, status FROM publisher")
        publishers = cursor.fetchall()    
        return render_template("publisher.html", publishers=publishers)
    return redirect(url_for('home'))

@app.route("/savePublisher", methods=['GET', 'POST'])
def savePublisher():
    if 'loggedin' in session and session['role'] == 'admin':  
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if request.method == 'POST' and 'name' in request.form and 'status' in request.form:
            name = request.form['name'] 
            status = request.form['status']             
            action = request.form['action']             
            if action == 'updatePublisher':
                publisherid = request.form['publisherid'] 
                cursor.execute('UPDATE publisher SET name = %s, status = %s WHERE publisherid = %s', (name, status, publisherid))
                mysql.connection.commit()        
            else: 
                cursor.execute('INSERT INTO publisher (`name`, `status`) VALUES (%s, %s)', (name, status))
                mysql.connection.commit()        
            return redirect(url_for('publisher'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form !'        
        return redirect(url_for('publisher'))
    return redirect(url_for('home'))

@app.route("/editPublisher", methods=['GET', 'POST'])
def editPublisher():
    if 'loggedin' in session and session['role'] == 'admin': 
        publisherid = request.args.get('publisherid') 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT publisherid, name, status FROM publisher WHERE publisherid = %s', (publisherid,))
        publishers = cursor.fetchall() 
        return render_template("edit_publisher.html", publishers=publishers)
    return redirect(url_for('home'))  

@app.route("/delete_publisher", methods=['GET'])
def delete_publisher():
    if 'loggedin' in session and session['role'] == 'admin':
        publisherid = request.args.get('publisherid') 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM publisher WHERE publisherid = %s', (publisherid,))
        mysql.connection.commit()   
        return redirect(url_for('publisher'))
    return redirect(url_for('home'))
    
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

