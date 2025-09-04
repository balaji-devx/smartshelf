from transformers import GPT2LMHeadModel, GPT2Tokenizer
import MySQLdb
import wikipedia
import re
import requests

# Initialize GPT-2 model and tokenizer
model_name = "gpt2"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# Predefined responses for common greetings and queries
predefined_responses = {
    'hi': "Hello! I'm your online librarian. How can I help you today?",
    'hello': "Hi there! Need help finding books or information?",
    'bro': "Sure thing, bro! What book or help are you looking for?",
    'hey': "Hey! What can I assist you with today?",
    'nanba': "Nanba, tell me what you're searching for!",
    'nanbi': "Nanbi, how can I help you today?",
    'library': "I'm here to assist you with books and PDFs. Just ask!",
    'help': "I'm here to help! You can ask me to find books, authors, or anything related to the library.",
    'நண்பா': "நண்பா நலமா! ஏதாவது தேடுறியா? சொல்லுங்க."
}

def get_wikipedia_summary(topic):
    """
    A more flexible Wikipedia summary function that handles topics intelligently
    without requiring manual topic definitions.
    """
    try:
        # Clean the topic by removing question marks and leading phrases
        cleaned_topic = topic.replace('?', '').strip()
        cleaned_topic = re.sub(r'^(tell me about|what is)\s+', '', cleaned_topic.lower()).strip()
        
        # First, try to get search suggestions
        search_results = wikipedia.search(cleaned_topic, results=5)
        
        if not search_results:
            return False, "I couldn't find information about that topic. Could you try rephrasing or being more specific?"
            
        # Check if the first result is a disambiguation page
        try:
            # Try getting summary of the first result
            first_result = search_results[0]
            page = wikipedia.page(first_result, auto_suggest=False)
            
            # If we successfully get a page, check if it's appropriate
            if any(category.lower() in page.categories for category in ['Adult', 'Mature', 'NSFW']):
                return True, "This topic may require more specific or appropriate context. Could you clarify what aspect you're interested in learning about?"
            
            # Get the summary
            summary = wikipedia.summary(first_result, sentences=3, auto_suggest=False)
            
            # Format response with topic categorization
            response = f"Here's what I found about {first_result}:\n\n{summary}\n\n"
            
            # Add context if there are other relevant topics
            if len(search_results) > 1:
                response += "There are also other related topics. Would you like to know about any of these instead?\n"
                for i, result in enumerate(search_results[1:], 1):
                    if result != first_result:
                        response += f"{i}. {result}\n"
            
            return True, response
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Clean up disambiguation options
            filtered_options = []
            for option in e.options[:5]:
                # Skip meta-pages and obvious non-relevant options
                if not any(skip in option.lower() for skip in [
                    '(disambiguation)', 
                    'list of', 
                    'index of',
                    'category:',
                    'template:',
                    'file:'
                ]):
                    filtered_options.append(option)
            
            if filtered_options:
                response = f"There are several topics related to '{cleaned_topic}'. Which one interests you?\n\n"
                for i, option in enumerate(filtered_options, 1):
                    response += f"{i}. {option}\n"
                return True, response
            
        except wikipedia.exceptions.PageError:
            return False, f"I couldn't find specific information about '{cleaned_topic}'. Could you try being more specific or using different terms?"
            
    except Exception as e:
        print(f"Wikipedia error: {str(e)}")
        error_message = "I encountered an issue while searching for information. "
        error_message += "Could you try rephrasing your question or being more specific?"
        return False, error_message

def get_books_by_genre_api(genre):
    """
    Fetches books from Google Books API as a fallback when database search fails.
    Args:
        genre (str): Genre or search term for books
    Returns:
        list: List of formatted book information
    """
    api_key = "AIzaSyCtFJR7lQPRyiZLKr8YuHKwRZYVXMScYFQ"
    url = f"https://www.googleapis.com/books/v1/volumes?q={genre}&key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        if 'items' in data:
            books = []
            for item in data['items']:
                book_info = item['volumeInfo']
                title = book_info.get('title', 'No title available')
                authors = ', '.join(book_info.get('authors', ['Unknown author']))
                link = book_info.get('infoLink', '#')
                # Format as HTML
                book_html = f"""
                <div class='book-item'>
                    <h3>{title}</h3>
                    <p>By: {authors}</p>
                    <a href='{link}' target='_blank' class='book-link'>View Details</a>
                </div>
                """
                books.append(book_html)
            return books
        return ["No books found in this genre."]
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        return ["Error: Unable to fetch books from the API."]

def fetch_available_books(mysql):
    """
    Retrieves all available books from the database.
    Args:
        mysql: MySQL database connection
    Returns:
        str: Formatted HTML response with available books
    """
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT bookid, name, no_of_copy, pdf_path
            FROM book
            WHERE no_of_copy > 0
            ORDER BY name
        """)
        results = cursor.fetchall()
        cursor.close()

        if results:
            response = "<div class='available-books'>"
            response += "<h2>Available Books:</h2>"
            for row in results:
                response += f"""
                <div class='book-item'>
                    <h3>{row['name']}</h3>
                    <p>Copies Available: {row['no_of_copy']}</p>
                    <a href='http://127.0.0.1:5000/static/books/{row['pdf_path']}' 
                       class='btn btn-primary' 
                       target='_blank'>
                        View PDF
                    </a>
                </div>
                """
            response += "</div>"
            return response
        return "No books are currently available. Would you like me to suggest some books?"
    except Exception as e:
        print(f"Database error: {str(e)}")
        return "Sorry, I couldn't fetch the available books right now."

def fetch_books_by_author(mysql, author_query):
    """
    Searches for books by a specific author in the database.
    Args:
        mysql: MySQL database connection
        author_query (str): Author name to search for
    Returns:
        str: Formatted HTML response with author's books
    """
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT book.bookid, book.name, book.pdf_path, author.name as author_name
            FROM book
            JOIN author ON book.authorid = author.authorid
            WHERE author.name LIKE %s
        """, (f"%{author_query}%",))
        results = cursor.fetchall()
        cursor.close()

        if results:
            response = f"<div class='author-books'>"
            response += f"<h2>Books by {results[0]['author_name']}:</h2>"
            for row in results:
                response += f"""
                <div class='book-item'>
                    <h3>{row['name']}</h3>
                    <a href='http://127.0.0.1:5000/static/books/{row['pdf_path']}' 
                       class='btn btn-primary' 
                       target='_blank'>
                        View PDF
                    </a>
                </div>
                """
            response += "</div>"
            return response
        return f"No books found by author '{author_query}'. Would you like to try another author?"
    except Exception as e:
        print(f"Database error: {str(e)}")
        return "Sorry, I couldn't search for books by this author."

def fetch_book_details(mysql, book_name):
    """
    Searches for specific book details in the database.
    Args:
        mysql: MySQL database connection
        book_name (str): Name of the book to search for
    Returns:
        str: Formatted HTML response with book details
    """
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT book.bookid, book.name, author.name AS author_name, 
                   publisher.name AS publisher_name, book.no_of_copy, 
                   book.status, book.pdf_path
            FROM book
            JOIN author ON book.authorid = author.authorid
            JOIN publisher ON book.publisherid = publisher.publisherid
            WHERE book.name LIKE %s
        """, (f"%{book_name}%",))
        results = cursor.fetchall()
        cursor.close()

        if results:
            response = "<div class='book-details'>"
            for row in results:
                response += f"""
                <div class='book-item'>
                    <h3>{row['name']}</h3>
                    <p>Author: {row['author_name']}</p>
                    <p>Publisher: {row['publisher_name']}</p>
                    <p>Copies Available: {row['no_of_copy']}</p>
                    <p>Status: {row['status']}</p>
                    <a href='http://127.0.0.1:5000/static/books/{row['pdf_path']}' 
                       class='btn btn-primary' 
                       target='_blank'>
                        View PDF
                    </a>
                </div>
                """
            response += "</div>"
            return response
        return f"Sorry, I couldn't find a book named '{book_name}'. Would you like to try another search?"
    except Exception as e:
        print(f"Database error: {str(e)}")
        return "Sorry, I couldn't fetch the book details."

def fetch_books_by_genre(mysql, genre):
    """
    Searches for books by genre in the database.
    Args:
        mysql: MySQL database connection
        genre (str): Genre to search for
    Returns:
        str: Formatted HTML response with books in the genre
    """
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT book.bookid, book.name, book.pdf_path, category.name as genre_name
            FROM book
            JOIN category ON book.categoryid = category.categoryid
            WHERE category.name LIKE %s
        """, (f"%{genre}%",))
        results = cursor.fetchall()
        cursor.close()

        if results:
            response = f"<div class='genre-books'>"
            response += f"<h2>Books in {results[0]['genre_name']}:</h2>"
            for row in results:
                response += f"""
                <div class='book-item'>
                    <h3>{row['name']}</h3>
                    <a href='http://127.0.0.1:5000/static/books/{row['pdf_path']}' 
                       class='btn btn-primary' 
                       target='_blank'>
                        View PDF
                    </a>
                </div>
                """
            response += "</div>"
            return response
        return None  # Return None to indicate no results found
    except Exception as e:
        print(f"Database error: {str(e)}")
        return "Sorry, I couldn't search for books in this genre."

def user_feedback(message, mysql):
    """
    Stores user feedback in the database.
    Args:
        message (str): Feedback message
        mysql: MySQL database connection
    Returns:
        str: Confirmation message
    """
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO feedback (message) VALUES (%s)", (message,))
        mysql.connection.commit()
        cursor.close()
        return "Thank you for your feedback! It helps us improve our service."
    except Exception as e:
        print(f"Database error: {str(e)}")
        return "Sorry, I couldn't save your feedback. Please try again later."

def generate_response(user_message, mysql):
    """
    Main function to generate responses based on user input.
    Args:
        user_message (str): User's input message
        mysql: MySQL database connection
    Returns:
        str: Formatted response to the user's query
    """
    # Normalize message
    normalized_message = user_message.lower().strip()
    
    # 1. Check predefined responses
    if normalized_message in predefined_responses:
        return predefined_responses[normalized_message]
    
    # 2. Handle book-related database queries
    if any(keyword in normalized_message for keyword in ['available books', 'show books', 'list books']):
        return fetch_available_books(mysql)
    
    if 'by' in normalized_message and 'books' in normalized_message:
        author_name = normalized_message.split('by')[-1].strip()
        return fetch_books_by_author(mysql, author_name)
    
    if 'find book' in normalized_message or 'search book' in normalized_message:
        book_name = normalized_message.replace('find book', '').replace('search book', '').strip()
        db_result = fetch_book_details(mysql, book_name)
        if not "Sorry" in db_result:
            return db_result
        
        # Fallback to Google Books API
        api_results = get_books_by_genre_api(book_name)
        if api_results and api_results[0] != "No books found in this genre.":
            response = "<div class='api-results'>"
            response += "<h2>Related books found online:</h2>"
            response += "".join(api_results)
            response += "</div>"
            return response
    
    # 3. Handle genre-specific queries
    if "books in" in normalized_message:
        genre = normalized_message.replace("books in", "").strip()
        db_result = fetch_books_by_genre(mysql, genre)
        
        if db_result is None:  # No results in database
            api_results = get_books_by_genre_api(genre)
            if api_results and api_results[0] != "No books found in this genre.":
                response = "<div class='api-results'>"
                response += f"<h2>Books in {genre} found online:</h2>"
                response += "".join(api_results)
                response += "</div>"
                return response
        else:
            return db_result
    
    # 4. Handle Wikipedia queries (only if explicitly requested)
    if normalized_message.startswith(("tell me about ", "what is ")):
        success, wiki_response = get_wikipedia_summary(user_message)
        if success:
            return wiki_response
    
    # 5. Handle feedback
    if "feedback" in normalized_message:
        feedback_message = normalized_message.replace("feedback", "").strip()
        if feedback_message:
            return user_feedback(feedback_message, mysql)
    
    # 6. Fallback to GPT-2
    try:
        inputs = tokenizer(normalized_message, return_tensors="pt", padding=True, truncation=True)
        outputs = model.generate(
            inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=50,  # Shorter length to prevent wandering
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3,  # Prevent 3-gram repetitions
            repetition_penalty=1.5,   # Penalize repetition
            temperature=0.7,          # Lower temperature for more focused output
            top_p=0.92                # Nucleus sampling to reduce randomness
        )
        
        # Decode and clean the response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove any repeated sentences
        sentences = response.split('.')
        unique_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in unique_sentences:
                unique_sentences.append(sentence)
        
        # Reconstruct the response
        clean_response = '. '.join(unique_sentences)
        if clean_response and not clean_response.endswith('.'):
            clean_response += '.'
            
        return clean_response
        
    except Exception as e:
        print(f"GPT-2 generation error: {str(e)}")
        return "I'm not sure how to help with that. Could you try rephrasing your question?"

        