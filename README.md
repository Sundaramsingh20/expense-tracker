# Expense Tracker (Mini Project)

A web app where users register, log in, and track their daily expenses with a
monthly chart, budget alerts and CSV export.

**Tech stack:** Python (Flask), SQLite, HTML, CSS, JavaScript (Chart.js)

## Features
- User registration and login (passwords stored as hashes, never plain text)
- Add and delete expenses with category and date
- Monthly total and month selector
- Doughnut chart of spending by category
- Monthly budget with a progress bar and warning at 80% / over 100%
- Live search in the expense table
- Export all expenses to CSV
- Each user can only see and delete their own expenses

## How to run
1. Install Python 3.9 or newer.
2. Open a terminal in this folder and install Flask:

       pip install -r requirements.txt

3. Start the app:

       python app.py

4. Open http://127.0.0.1:5000 in your browser, create an account and log in.

The database file `expenses.db` is created automatically on first run.
(The chart needs internet because Chart.js loads from a CDN.)

## Project structure
    app.py              Flask backend: routes, database, login logic
    requirements.txt    Python dependencies
    templates/          HTML pages (Jinja2)
        base.html       Common layout (navbar, flash messages)
        login.html
        register.html
        dashboard.html  Main page: summary, form, chart, table
    static/
        style.css       Styling
        app.js          Chart, search filter, delete confirmation
    expenses.db         SQLite database (created on first run)

## Database design
- **users**(id, username, password_hash, budget)
- **expenses**(id, user_id -> users.id, title, amount, category, expense_date)

## Future scope
Edit expenses, income tracking, recurring expenses, email reports,
mobile app, deploying online.
