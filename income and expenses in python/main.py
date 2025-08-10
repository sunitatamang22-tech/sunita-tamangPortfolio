import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import csv
from fpdf import FPDF

# createating a database 
conn = sqlite3.connect("expense_tracker.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Expenses (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  description TEXT,
  amount REAL,
  category TEXT,
  date_time DATETIME,
  FOREIGN KEY (user_id) REFERENCES Users(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Budgets (
  user_id INTEGER PRIMARY KEY,
  budget REAL,
  FOREIGN KEY (user_id) REFERENCES Users(id)
)
''')
conn.commit()

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("900x700")
        self.user_id = None
        self.expense_to_update = None

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Arial', 12), padding=6)
        self.style.configure('TLabel', font=('Arial', 12), padding=5)
        self.style.configure('TEntry', font=('Arial', 12), padding=5)
        self.style.configure('Treeview.Heading', font=('Arial', 12, 'bold'))

        self.login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def login_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Login to Expense Tracker", font=(
            "Arial", 20, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
        ttk.Label(frame, text="Username:").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(frame, width=30)
        self.username_entry.grid(row=1, column=1)

        ttk.Label(frame, text="Password:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1)

        ttk.Button(frame, text="Login", command=self.login_user).grid(
            row=3, column=0, pady=15, sticky=tk.E)
        ttk.Button(frame, text="Register", command=self.register_screen).grid(
            row=3, column=1, pady=15, sticky=tk.W)

    def register_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Register", font=("Arial", 20, "bold")
                  ).grid(row=0, column=0, columnspan=2, pady=20)
        ttk.Label(frame, text="Username:").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.reg_username_entry = ttk.Entry(frame, width=30)
        self.reg_username_entry.grid(row=1, column=1)

        ttk.Label(frame, text="Password:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.reg_password_entry = ttk.Entry(frame, show="*", width=30)
        self.reg_password_entry.grid(row=2, column=1)

        ttk.Button(frame, text="Register", command=self.register_user).grid(
            row=3, column=0, pady=15, sticky=tk.E)
        ttk.Button(frame, text="Back", command=self.login_screen).grid(
            row=3, column=1, pady=15, sticky=tk.W)

    def register_user(self):
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            cursor.execute(
                "INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")
            self.login_screen()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")

    def login_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        cursor.execute(
            "SELECT id FROM Users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            self.user_id = user[0]
            messagebox.showinfo("Success", f"Welcome, {username}!")
            self.main_screen()
        else:
            messagebox.showerror("Error", "Invalid credentials.")

    def main_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Expense Tracker", font=(
            "Arial", 20, "bold")).pack(pady=20)

        ttk.Button(frame, text="Add Expense",
                   command=self.add_expense_screen).pack(pady=10, fill=tk.X)
        ttk.Button(frame, text="View Expenses",
                   command=self.view_expenses_screen).pack(pady=10, fill=tk.X)
        ttk.Button(frame, text="Set Budget",
                   command=self.set_budget_screen).pack(pady=10, fill=tk.X)
        ttk.Button(frame, text="Generate Report",
                   command=self.generate_report_screen).pack(pady=10, fill=tk.X)
        ttk.Button(frame, text="Logout", command=self.logout).pack(
            pady=20, fill=tk.X)

        self.load_budget()
        if self.budget is not None:
            total_expenses = self.get_monthly_expenses()
            budget_status = f"Budget: ${ self.budget} | Spent: ${total_expenses}"
            color = "red" if total_expenses > self.budget else "green"
            status_label = ttk.Label(
                frame, text=budget_status, foreground=color, font=("Arial", 14))
            status_label.pack(pady=10)

            # Showing the exceeded status explicitly
            if total_expenses > self.budget:
                exceeded_label = ttk.Label(
                    frame, text="Warning: Budget Exceeded!", foreground="red", font=("Arial", 12, "bold"))
                exceeded_label.pack(pady=5)

    def add_expense_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Add New Expense", font=(
            "Arial", 20, "bold")).pack(pady=10)

        ttk.Label(frame, text="Description:").pack(anchor=tk.W)
        self.exp_description = ttk.Entry(frame, width=40)
        self.exp_description.pack()

        ttk.Label(frame, text="Amount:").pack(anchor=tk.W)
        self.exp_amount = ttk.Entry(frame, width=40)
        self.exp_amount.pack()

        ttk.Label(frame, text="Category:").pack(anchor=tk.W)
        self.exp_category = ttk.Combobox(frame, values=[
            "Food", "Transport", "Entertainment", "Utilities", "Others"], width=37)
        self.exp_category.set("Food")  # Set default category value
        self.exp_category.pack()

        ttk.Button(frame, text="Add", command=self.add_expense).pack(pady=10)
        ttk.Button(frame, text="Back", command=self.main_screen).pack()

    def add_expense(self):
        description = self.exp_description.get()
        amount = self.exp_amount.get()
        category = self.exp_category.get()
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not description or not amount or not category:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            amount = float(amount)
            cursor.execute('''INSERT INTO Expenses (user_id, description, amount, category, date_time) VALUES (?, ?, ?, ?, ?)''',
                           (self.user_id, description, amount, category, date_time))
            conn.commit()

            # Budget check
            cursor.execute(
                "SELECT budget FROM Budgets WHERE user_id = ?", (self.user_id,))
            budget = cursor.fetchone()
            if budget and amount > budget[0]:
                messagebox.showwarning(
                    "Budget Alert", "You have exceeded your budget limit!")

            messagebox.showinfo("Success", "Expense added successfully!")
            self.main_screen()
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number.")

    def view_expenses_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="View Expenses", font=(
            "Arial", 20, "bold")).pack(pady=10)

        self.search_var = ttk.Entry(frame, width=40)
        self.search_var.pack(pady=10)
        ttk.Button(frame, text="Search by Category",
                   command=self.search_expenses).pack(pady=5)
        ttk.Button(frame, text="Search by Date",
                   command=self.search_by_date).pack(pady=5)
        ttk.Button(frame, text="Back", command=self.main_screen).pack(pady=10)

        columns = ("Description", "Amount", "Category",
                   "Date/Time", "Update", "Delete")
        self.expense_tree = ttk.Treeview(
            frame, columns=columns, show="headings")
        self.expense_tree.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            self.expense_tree.heading(col, text=col)

        self.expense_tree.column("Update", width=80)
        self.expense_tree.column("Delete", width=80)

        hsb = ttk.Scrollbar(frame, orient="horizontal",
                            command=self.expense_tree.xview)
        hsb.pack(side="bottom", fill="x")

        self.expense_tree.configure(xscrollcommand=hsb.set)

        self.update_expense_tree()

        # event for update and delete
        self.expense_tree.bind("<ButtonRelease-1>", self.on_expense_tree_click)

    def update_expense_screen(self, expense_id):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        self.expense_to_update = expense_id

        # call data from the database
        cursor.execute(
            '''SELECT description, amount, category FROM Expenses WHERE id = ?''', (expense_id,))
        expense = cursor.fetchone()

        ttk.Label(frame, text="Update Expense", font=(
            "Arial", 20, "bold")).pack(pady=10)

        ttk.Label(frame, text="Description:").pack(anchor=tk.W)
        self.exp_description = ttk.Entry(frame, width=40)
        # Pre-fill with current description
        self.exp_description.insert(0, expense[0])
        self.exp_description.pack()

        ttk.Label(frame, text="Amount:").pack(anchor=tk.W)
        self.exp_amount = ttk.Entry(frame, width=40)
        self.exp_amount.insert(0, expense[1])  # Pre-fill with current amount
        self.exp_amount.pack()

        ttk.Label(frame, text="Category:").pack(anchor=tk.W)
        self.exp_category = ttk.Combobox(frame, values=[
                                         "Food", "Transport", "Entertainment", "Utilities", "Others"], width=37)
        self.exp_category.set(expense[2])  # Pre-fill with current category
        self.exp_category.pack()

        ttk.Button(frame, text="Save Changes",
                   command=self.save_updated_expense).pack(pady=10)
        ttk.Button(frame, text="Back",
                   command=self.view_expenses_screen).pack()

    # for saving updated data

    def save_updated_expense(self):
        description = self.exp_description.get()
        amount = self.exp_amount.get()
        category = self.exp_category.get()

        if not description or not amount or not category:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            amount = float(amount)
            cursor.execute('''UPDATE Expenses SET description = ?, amount = ?, category = ? WHERE id = ?''',
                           (description, amount, category, self.expense_to_update))
            conn.commit()

            messagebox.showinfo("Success", "Expense updated successfully!")
            self.view_expenses_screen()
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number.")

    # for delete record
    def delete_expense(self, expense_id):
        confirm = messagebox.askyesno(
            "Confirm", "Are you sure you want to delete this expense?")
        if confirm:
            cursor.execute(
                '''DELETE FROM Expenses WHERE id = ?''', (expense_id,))
            conn.commit()
            messagebox.showinfo("Success", "Expense deleted successfully!")
            self.view_expenses_screen()

    # update and delete button
    def update_expense_tree(self):
        for row in self.expense_tree.get_children():
            self.expense_tree.delete(row)

        cursor.execute(
            '''SELECT id, description, amount, category, date_time FROM Expenses WHERE user_id = ?''', (self.user_id,))
        expenses = cursor.fetchall()

        for expense in expenses:
            self.expense_tree.insert("", "end", text=expense[0], values=(
                expense[1], expense[2], expense[3], expense[4], "Update", "Delete"))

        for item in self.expense_tree.get_children():
            self.expense_tree.item(item, tags="clickable")

    #for update and delete

    def on_expense_tree_click(self, event):
        selected_item = self.expense_tree.focus()
        if selected_item:
            item_values = self.expense_tree.item(selected_item, "values")
            col = self.expense_tree.identify_column(event.x)
            if col == "#5" and "Update" in item_values[-2]:  # Update column
                expense_id = self.expense_tree.item(selected_item, "text")
                self.update_expense_screen(expense_id)
            elif col == "#6" and "Delete" in item_values[-1]:  # Delete column
                expense_id = self.expense_tree.item(selected_item, "text")
                self.delete_expense(expense_id)

    def search_expenses(self):
        search_text = self.search_var.get().lower()
        if not search_text:
            self.update_expense_tree()
            return

        cursor.execute('''SELECT id, description, amount, category, date_time FROM Expenses WHERE user_id = ? AND category LIKE ?''',
                       (self.user_id, f"%{search_text}%"))
        expenses = cursor.fetchall()

        for row in self.expense_tree.get_children():
            self.expense_tree.delete(row)

        for expense in expenses:
            self.expense_tree.insert("", "end", values=(
                expense[1], expense[2], expense[3], expense[4], "Update", "Delete"))

    def search_by_date(self):
        search_text = self.search_var.get()
        if not search_text:
            self.update_expense_tree()
            return

        cursor.execute('''SELECT id, description, amount, category, date_time FROM Expenses WHERE user_id = ? AND date_time LIKE ?''',
                       (self.user_id, f"%{search_text}%"))
        expenses = cursor.fetchall()

        for row in self.expense_tree.get_children():
            self.expense_tree.delete(row)

        for expense in expenses:
            self.expense_tree.insert("", "end", values=(
                expense[1], expense[2], expense[3], expense[4], "Update", "Delete"))

    def set_budget_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Set Budget", font=(
            "Arial", 20, "bold")).pack(pady=10)

        ttk.Label(frame, text="Budget Amount:").pack(anchor=tk.W)
        self.budget_entry = ttk.Entry(frame, width=30)
        self.budget_entry.pack()

        ttk.Button(frame, text="Set Budget",
                   command=self.set_budget).pack(pady=10)
        ttk.Button(frame, text="Back", command=self.main_screen).pack()

    def set_budget(self):
        budget = self.budget_entry.get()

        if not budget:
            messagebox.showerror("Error", "Budget amount is required.")
            return

        try:
            budget = float(budget)
            cursor.execute(
                "INSERT OR REPLACE INTO Budgets (user_id, budget) VALUES (?, ?)", (self.user_id, budget))
            conn.commit()
            messagebox.showinfo("Success", "Budget set successfully!")
            self.main_screen()
        except ValueError:
            messagebox.showerror("Error", "Budget must be a number.")

    def generate_report_screen(self):
        self.clear_screen()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Generate Report", font=(
            "Arial", 20, "bold")).pack(pady=10)

        ttk.Button(frame, text="Export to PDF",
                   command=self.export_to_pdf).pack(pady=10)
        ttk.Button(frame, text="Back", command=self.main_screen).pack()

    def export_to_pdf(self):
        cursor.execute(
            '''SELECT description, amount, category, date_time FROM Expenses WHERE user_id = ?''', (self.user_id,))
        expenses = cursor.fetchall()

        if not expenses:
            messagebox.showerror("Error", "No expenses to export.")
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Expense Report", ln=True, align="C")
        pdf.ln(10)

        pdf.cell(40, 10, "Description", border=1)
        pdf.cell(40, 10, "Amount", border=1)
        pdf.cell(40, 10, "Category", border=1)
        pdf.cell(60, 10, "Date/Time", border=1)
        pdf.ln()

        for expense in expenses:
            pdf.cell(40, 10, expense[0], border=1)
            pdf.cell(40, 10, str(expense[1]), border=1)
            pdf.cell(40, 10, expense[2], border=1)
            pdf.cell(60, 10, expense[3], border=1)
            pdf.ln()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            pdf.output(file_path)
            messagebox.showinfo("Success", "Report exported successfully!")

    def load_budget(self):
        cursor.execute(
            "SELECT budget FROM Budgets WHERE user_id = ?", (self.user_id,))
        result = cursor.fetchone()
        self.budget = result[0] if result else None

    def get_monthly_expenses(self):
        current_month_start = datetime.now().replace(
            day=1).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT SUM(amount) FROM Expenses WHERE user_id = ? AND date_time >= ?",
                       (self.user_id, current_month_start))
        total = cursor.fetchone()[0]
        return total if total else 0.0

    def logout(self):
        self.user_id = None
        self.login_screen()


# main function
if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()