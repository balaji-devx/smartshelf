# SmartShelf - An AI Automated Library Website

Welcome to **SmartShelf**, an AI-powered library automation system designed to streamline book management and provide intelligent eBook recommendations using GPT-2.

---

## **Features**
- **User-Friendly Interface**: Search and browse books with an aesthetically pleasing design.
- **AI Integration**: GPT-2 generates conversational responses and suggests books based on user input.
- **Book Management**: Add, update, or remove books in the library seamlessly.
- **User Authentication**: Secure login and registration for users and admins.
- **Dynamic Interaction**: Interactive features like search suggestions and pop-ups using JavaScript.

---

## **Getting Started**

Follow this tutorial to set up and use SmartShelf.

### **1. Prerequisites**
Ensure the following are installed on your system:
- Python 3.8+
- Flask Framework
- Flask-MySQLdb
- MySQL (using XAMPP or a standalone installation)
- A browser to access the web application

Optional tools:
- Google Colab (for GPT-2 integration and analytics)
- GitHub Pages (for hosting the frontend)

---

### **2. Installation**

#### **Clone the Repository**
```bash
$ git clone https://github.com/your-repository/smartshelf.git
$ cd smartshelf
```

#### **Set Up a Virtual Environment**
```bash
$ python -m venv venv
$ source venv/bin/activate   # On Windows: venv\Scripts\activate
```

#### **Install Dependencies**
```bash
$ pip install -r requirements.txt
```

---

### **3. Database Setup**

#### **Create the Database**
1. Open MySQL (e.g., via phpMyAdmin or CLI).
2. Create a database named `library-system`.
3. Run the SQL scripts in `schema.sql` (included in the repository) to set up tables like `user`, `book`, `author`, and `publisher`.

#### **Configure Database Credentials**
Update the `config.py` file with your MySQL credentials:
```python
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'Balaji%402005'
MYSQL_DB = 'library-system'
MYSQL_HOST = 'localhost'
```

---

### **4. Running the Application**

#### **Start the Flask Server**
```bash
$ flask run
```
By default, the app runs on `http://127.0.0.1:5000/`.

#### **Access the Application**
1. Open your browser and go to `http://127.0.0.1:5000/`.
2. Use the homepage to navigate to login or register as a user/admin.

---

### **5. Usage**

#### **User Features**
- **Search Books**: Enter keywords to find books.
- **View Book Details**: Click on any book to see more information.
- **eBook Suggestions**: Get AI-generated recommendations based on your queries.

#### **Admin Features**
- **Manage Books**: Add, update, or delete books in the library.
- **Monitor Users**: View and manage registered users.

---

### **6. Project Structure**

```plaintext
SmartShelf/
├── app.py            # Main Flask application
├── gpt2.py           # GPT-2 functionalities
├── static/           # CSS, JavaScript, images
│   ├── css/
│   ├── js/
│   └── books/        # Uploaded eBooks
├── templates/        # HTML templates (Flask rendering)
├── modules/          # Flask Blueprints (user, book, GPT-2, etc.)
├── requirements.txt  # Python dependencies
└── README.md         # Project tutorial
```

---

### **7. Troubleshooting**

#### **Common Issues**
1. **Database Connection Error**:
   - Ensure MySQL is running and credentials are correct.
2. **Dependencies Not Found**:
   - Run `pip install -r requirements.txt` again.
3. **Static Files Not Loading**:
   - Check the paths in your `static` folder and Flask templates.

#### **Logs**
Check the terminal logs for error messages while running the Flask server.

---

### **8. Contributing**
We welcome contributions! Feel free to fork the repository, make changes, and create a pull request.

---

### **9. License**
This project is licensed under the MIT License. See `LICENSE` for details.

---

Happy learning and reading with SmartShelf! 📚✨
