import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image
import io

# Load CSS from a file
def load_css(file_name):
    with open(file_name, "r") as f:
        return f"<style>{f.read()}</style>"

# Load and inject the CSS
css = load_css("styles.css")
st.markdown(css, unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    # Create categories table
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, budget REAL)''')
    # Create table for total available money
    c.execute('''CREATE TABLE IF NOT EXISTS total_money
                 (id INTEGER PRIMARY KEY, total REAL)''')
    # Create table for actual expenses
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER, amount REAL, 
                  details TEXT, timestamp TEXT, receipt BLOB, FOREIGN KEY(category_id) REFERENCES categories(id))''')
    # Initialize total money if not present
    c.execute('SELECT COUNT(*) FROM total_money')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO total_money (id, total) VALUES (1, 0)')
        conn.commit()
    conn.close()

# Fetch total available money
def get_total_money():
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('SELECT total FROM total_money WHERE id=1')
    total = c.fetchone()[0]
    conn.close()
    return total

# Update total available money
def update_total_money(new_total):
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('UPDATE total_money SET total = ? WHERE id = 1', (new_total,))
    conn.commit()
    conn.close()

# Fetch all categories
def get_categories():
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('SELECT * FROM categories')
    categories = c.fetchall()
    conn.close()
    return categories

# Add a new category
def add_category(name, budget):
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('INSERT INTO categories (name, budget) VALUES (?, ?)', (name, budget))
    conn.commit()
    conn.close()

# Update a category's budget
def update_category(category_id, new_budget):
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('UPDATE categories SET budget = ? WHERE id = ?', (new_budget, category_id))
    conn.commit()
    conn.close()

# Delete a category
def delete_category(category_id):
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()

# Add an actual expense
def add_expense(category_id, amount, details, timestamp, receipt):
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (category_id, amount, details, timestamp, receipt) VALUES (?, ?, ?, ?, ?)',
              (category_id, amount, details, timestamp, receipt))
    conn.commit()
    conn.close()

# Fetch actual expenses for a category
def get_expenses(category_id):
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('SELECT amount, details, timestamp FROM expenses WHERE category_id = ?', (category_id,))
    expenses = c.fetchall()
    conn.close()
    return expenses

# Calculate total projected expense
def calculate_total_expense():
    categories = get_categories()
    total_expense = sum([cat[2] for cat in categories])
    return total_expense

# Calculate total spent for a category
def calculate_total_spent(category_id):
    conn = sqlite3.connect('budgeting_app.db')
    c = conn.cursor()
    c.execute('SELECT SUM(amount) FROM expenses WHERE category_id = ?', (category_id,))
    total_spent = c.fetchone()[0]
    if total_spent is None:
        total_spent = 0
    conn.close()
    return total_spent

# Initialize database
init_db()

# Initialize session state
if 'total_money' not in st.session_state:
    st.session_state['total_money'] = get_total_money()

if 'categories' not in st.session_state:
    st.session_state['categories'] = get_categories()

# Streamlit UI
st.title("Budgeting App")

# Fetch the total available money
total_money = st.session_state['total_money']

# Calculate the total projected expense
total_expense = calculate_total_expense()

# Calculate the remaining available money
available_money = total_money - total_expense

# Display Total Money Available (Top Right)
st.sidebar.header(f"Available Money: ${available_money:.2f}")

# Allow user to update the total available money
new_total_money = st.sidebar.number_input("Set Total Money Available", value=total_money, step=10.0)
if st.sidebar.button("Update Total Money"):
    update_total_money(new_total_money)
    st.session_state['total_money'] = new_total_money
    st.session_state['categories'] = get_categories()  # Refresh categories

# Display Total Projected Expense (Left Sidebar)
st.sidebar.header(f"Total Projected Expense: ${total_expense:.2f}")

# Manage Categories in Sidebar
st.sidebar.subheader("Manage Categories")

# Add a new category in the sidebar
with st.sidebar.form("Add Category"):
    category_name = st.text_input("Category Name")
    category_budget = st.number_input("Budget", min_value=0.0, step=10.0)
    if st.form_submit_button("Add Category"):
        add_category(category_name, category_budget)
        st.session_state['categories'] = get_categories()  # Refresh categories

# Summary of Categories and Remaining Budget
st.sidebar.subheader("Category Summary")
categories = st.session_state['categories']
if categories:
    for cat in categories:
        total_spent = calculate_total_spent(cat[0])
        remaining_budget = cat[2] - total_spent
        st.sidebar.write(f"{cat[1]}: ${remaining_budget:.2f} remaining")
else:
    st.sidebar.write("No categories yet.")

# Main Body - Display Categories and Actual Expenses
col1, col2 = st.columns(2)

# Left Column - Display and Edit Existing Categories
with col1:
    st.header("Created Categories")
    if categories:
        for cat in categories:
            st.subheader(cat[1])
            new_budget = st.number_input("Budget", value=cat[2], key=f"budget_{cat[0]}")
            if st.button("Update Budget", key=f"update_{cat[0]}"):
                update_category(cat[0], new_budget)
                st.session_state['categories'] = get_categories()  # Refresh categories
            if st.button("Delete", key=f"del_{cat[0]}"):
                delete_category(cat[0])
                st.session_state['categories'] = get_categories()  # Refresh categories
            total_spent = calculate_total_spent(cat[0])
            st.write(f"Total Spent: ${total_spent:.2f}")
            remaining_budget = new_budget - total_spent
            st.write(f"Remaining Budget: ${remaining_budget:.2f}")
    else:
        st.write("Add categories")

# Right Column - Actual Expenses
with col2:
    st.header("Actual Expenses")
    if categories:
        category_names = [cat[1] for cat in categories]
        selected_category = st.selectbox("Select a Category", category_names)
        selected_category_id = [cat[0] for cat in categories if cat[1] == selected_category][0]

        st.subheader(f"Add Expense for {selected_category}")
        with st.form("Add Expense"):
            expense_amount = st.number_input("Amount", min_value=0.0, step=1.0)
            expense_details = st.text_input("Details")
            receipt_image = st.file_uploader("Upload Receipt (optional)", type=["png", "jpg", "jpeg"])
            if receipt_image is not None:
                image_bytes = receipt_image.read()
            else:
                image_bytes = None
            submit_button = st.form_submit_button("Add Expense")
            if submit_button:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                add_expense(selected_category_id, expense_amount, expense_details, timestamp, image_bytes)
                st.success("Expense added successfully!")
                st.session_state['categories'] = get_categories()  # Refresh categories

        # Display existing expenses for the selected category
        st.write(f"Existing Expenses for {selected_category}:")
        expenses = get_expenses(selected_category_id)
        for exp in expenses:
            st.write(f"- {exp[0]:.2f} USD on {exp[2]} for {exp[1]}")
    else:
        st.write("Add categories")
