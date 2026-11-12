
# Part 1: Imports, Password Security and Account Class

import csv
import hashlib
import json
import os
import secrets
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

ACCOUNTS_FILE = "accounts.csv"
TRANSACTIONS_FILE = "transactions.csv"
ANNUAL_INTEREST_RATE = 0.05


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"),
        salt.encode("utf-8"), 200_000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password, stored_hash):
    try:
        salt, expected_digest = stored_hash.split("$", 1)
    except ValueError:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"),
        salt.encode("utf-8"), 200_000
    ).hex()

    return secrets.compare_digest(actual_digest, expected_digest)


class Account:
    def __init__(self, username, password_hash, balance=0.0,
                 account_number="", transactions=None):

        self.username = username
        self.password_hash = password_hash
        self.balance = float(balance)
        self.account_number = account_number
        self.transactions = transactions or []

    def add_transaction(self, kind, amount):
        transaction = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": kind,
            "amount": float(amount),
            "balance": self.balance,
        }

        self.transactions.append(transaction)
        return transaction

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        self.balance += amount
        return self.add_transaction("Deposit", amount)

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        if amount > self.balance:
            raise ValueError("Insufficient balance.")

        self.balance -= amount
        return self.add_transaction("Withdrawal", amount)

    def annual_interest(self):
        return self.balance * ANNUAL_INTEREST_RATE


# Part 2: Banking System and CSV Storage

class BankingSystem:
    def __init__(self):
        self.accounts = {}
        self.load_accounts()

    def load_accounts(self):
        if not os.path.exists(ACCOUNTS_FILE):
            return

        try:
            with open(ACCOUNTS_FILE, "r", newline="",
                      encoding="utf-8") as file:

                for row in csv.DictReader(file):
                    try:
                        transactions = json.loads(
                            row.get("transactions", "[]") or "[]"
                        )

                        account = Account(
                            username=row["username"],
                            password_hash=row["password_hash"],
                            balance=float(row["balance"]),
                            account_number=row.get("account_number", ""),
                            transactions=transactions
                        )

                        self.accounts[account.username] = account

                    except (KeyError, ValueError, json.JSONDecodeError):
                        continue

        except OSError as error:
            messagebox.showerror(
                "File Error",
                f"Could not load accounts.csv:\n{error}"
            )

    def save_accounts(self):
        with open(ACCOUNTS_FILE, "w", newline="",
                  encoding="utf-8") as file:

            fields = [
                "username", "password_hash", "balance",
                "account_number", "transactions"
            ]

            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()

            for account in self.accounts.values():
                writer.writerow({
                    "username": account.username,
                    "password_hash": account.password_hash,
                    "balance": f"{account.balance:.2f}",
                    "account_number": account.account_number,
                    "transactions": json.dumps(account.transactions)
                })

    def append_transaction(self, account, transaction):
        new_file = not os.path.exists(TRANSACTIONS_FILE)

        with open(TRANSACTIONS_FILE, "a", newline="",
                  encoding="utf-8") as file:

            fields = [
                "Username", "Transaction Type",
                "Amount", "Balance", "Date"
            ]

            writer = csv.DictWriter(file, fieldnames=fields)

            if new_file or os.path.getsize(TRANSACTIONS_FILE) == 0:
                writer.writeheader()

            writer.writerow({
                "Username": account.username,
                "Transaction Type": transaction["type"],
                "Amount": f'{transaction["amount"]:.2f}',
                "Balance": f'{transaction["balance"]:.2f}',
                "Date": transaction["date"]
            })

    def create_account(self, username, password):
        username = username.strip()

        if not username or not password:
            raise ValueError("Enter both username and password.")

        if username in self.accounts:
            raise ValueError("That username already exists.")

        account = Account(
            username=username,
            password_hash=hash_password(password),
            account_number=str(
                int(datetime.now().timestamp() * 1000000)
            )[-10:]
        )

        self.accounts[username] = account
        self.save_accounts()

        return account

    def login(self, username, password):
        account = self.accounts.get(username.strip())

        if account is None or not verify_password(
            password, account.password_hash
        ):
            raise ValueError("Invalid username or password.")

        return account

    def delete_account(self, username):
        self.accounts.pop(username, None)
        self.save_accounts()

        if os.path.exists(TRANSACTIONS_FILE):

            with open(TRANSACTIONS_FILE, "r", newline="",
                      encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            with open(TRANSACTIONS_FILE, "w", newline="",
                      encoding="utf-8") as file:

                fields = [
                    "Username", "Transaction Type",
                    "Amount", "Balance", "Date"
                ]

                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()

                writer.writerows(
                    row for row in rows
                    if row.get("Username") != username
                )

# Part 3: Tkinter GUI and Login Screen

class BankingApp:
    def __init__(self, root):
        self.root = root
        self.bank = BankingSystem()

        self.root.title("Python Bank Management System")
        self.root.geometry("760x620")
        self.root.minsize(650, 550)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TButton",
            font=("Arial", 10, "bold"),
            padding=8
        )

        style.configure(
            "TLabel",
            font=("Arial", 10)
        )

        style.configure(
            "Title.TLabel",
            font=("Arial", 22, "bold"),
            foreground="white",
            background="#17345c"
        )

        style.configure(
            "Heading.TLabel",
            font=("Arial", 15, "bold")
        )

        style.configure(
            "Balance.TLabel",
            font=("Arial", 18, "bold"),
            foreground="#1769aa"
        )

        self.build_home()

    def build_home(self):
        header = ttk.Frame(self.root)
        header.pack(fill="x")

        title = ttk.Label(
            header,
            text="PYTHON BANK",
            style="Title.TLabel",
            anchor="center",
            padding=18
        )

        title.pack(fill="x")

        notebook = ttk.Notebook(self.root)
        notebook.pack(
            fill="both",
            expand=True,
            padx=45,
            pady=35
        )

        create_tab = ttk.Frame(notebook, padding=30)
        login_tab = ttk.Frame(notebook, padding=30)

        notebook.add(create_tab, text="Create Account")
        notebook.add(login_tab, text="Login")

        # CREATE ACCOUNT

        ttk.Label(
            create_tab,
            text="Create New Account",
            style="Heading.TLabel"
        ).pack(pady=12)

        ttk.Label(create_tab, text="Username").pack()

        self.create_username = ttk.Entry(
            create_tab, width=32
        )
        self.create_username.pack(pady=7)

        ttk.Label(create_tab, text="Password").pack()

        self.create_password = ttk.Entry(
            create_tab, width=32, show="*"
        )
        self.create_password.pack(pady=7)

        ttk.Button(
            create_tab,
            text="Create Account",
            command=self.create_account
        ).pack(pady=18)

        # LOGIN

        ttk.Label(
            login_tab,
            text="User Login",
            style="Heading.TLabel"
        ).pack(pady=12)

        ttk.Label(login_tab, text="Username").pack()

        self.login_username = ttk.Entry(
            login_tab, width=32
        )
        self.login_username.pack(pady=7)

        ttk.Label(login_tab, text="Password").pack()

        self.login_password = ttk.Entry(
            login_tab, width=32, show="*"
        )
        self.login_password.pack(pady=7)

        self.show_password_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            login_tab,
            text="Show password",
            variable=self.show_password_var,
            command=self.toggle_password
        ).pack(pady=4)

        ttk.Button(
            login_tab,
            text="Login",
            command=self.login
        ).pack(pady=18)

    def toggle_password(self):
        self.login_password.configure(
            show="" if self.show_password_var.get() else "*"
        )

    def create_account(self):
        try:
            account = self.bank.create_account(
                self.create_username.get(),
                self.create_password.get()
            )

            messagebox.showinfo(
                "Account Created",
                f"Account created successfully!\n"
                f"Username: {account.username}\n"
                f"Account number: {account.account_number}",
                parent=self.root
            )

            self.create_username.delete(0, tk.END)
            self.create_password.delete(0, tk.END)

        except (ValueError, OSError) as error:
            messagebox.showerror(
                "Error", str(error), parent=self.root
            )

    def login(self):
        try:
            account = self.bank.login(
                self.login_username.get(),
                self.login_password.get()
            )

            self.login_password.delete(0, tk.END)
            self.open_dashboard(account)

        except ValueError as error:
            messagebox.showerror(
                "Login Failed", str(error), parent=self.root
            )


# Part 4: Dashboard, Deposit and Withdrawal

    def open_dashboard(self, account):
        dashboard = tk.Toplevel(self.root)

        dashboard.title(
            f"{account.username} - Bank Dashboard"
        )
        dashboard.geometry("650x610")
        dashboard.transient(self.root)

        ttk.Label(
            dashboard,
            text=f"Welcome, {account.username}",
            style="Heading.TLabel"
        ).pack(pady=18)

        balance_label = ttk.Label(
            dashboard,
            style="Balance.TLabel"
        )
        balance_label.pack(pady=10)

        def refresh_balance():
            balance_label.config(
                text=f"Balance: ₹ {account.balance:,.2f}"
            )

        refresh_balance()

        ttk.Button(
            dashboard,
            text="Deposit Money",
            command=lambda: self.amount_dialog(
                dashboard, account, "Deposit",
                account.deposit, refresh_balance
            )
        ).pack(pady=6)

        ttk.Button(
            dashboard,
            text="Withdraw Money",
            command=lambda: self.amount_dialog(
                dashboard, account, "Withdrawal",
                account.withdraw, refresh_balance
            )
        ).pack(pady=6)

        ttk.Button(
            dashboard,
            text="Check Balance",
            command=lambda: messagebox.showinfo(
                "Balance",
                f"Available balance: ₹ {account.balance:,.2f}",
                parent=dashboard
            )
        ).pack(pady=6)

        ttk.Button(
            dashboard,
            text="Mini Statement (Last 5)",
            command=lambda: self.show_mini_statement(
                dashboard, account
            )
        ).pack(pady=6)

        ttk.Button(
            dashboard,
            text="Account Summary",
            command=lambda: self.show_account_summary(
                dashboard, account
            )
        ).pack(pady=6)

        ttk.Button(
            dashboard,
            text="Calculate 5% Annual Interest",
            command=lambda: self.show_interest(
                dashboard, account
            )
        ).pack(pady=6)

        ttk.Button(
            dashboard,
            text="Delete Account",
            command=lambda: self.delete_account(
                dashboard, account
            )
        ).pack(pady=6)

        ttk.Button(
            dashboard,
            text="Logout",
            command=dashboard.destroy
        ).pack(pady=16)

    def amount_dialog(
        self, parent, account, title,
        operation, refresh_balance
    ):
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("350x190")
        dialog.transient(parent)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text=f"Enter {title} Amount",
            style="Heading.TLabel"
        ).pack(pady=18)

        amount_entry = ttk.Entry(dialog, width=25)
        amount_entry.pack(pady=8)
        amount_entry.focus_set()

        def submit():
            try:
                value = float(amount_entry.get().strip())

                if value <= 0:
                    raise ValueError(
                        "Amount must be greater than zero."
                    )

                transaction = operation(value)

                self.bank.append_transaction(
                    account, transaction
                )

                self.bank.save_accounts()
                refresh_balance()

                messagebox.showinfo(
                    "Successful",
                    f"{title} successful.\n"
                    f"New balance: ₹ {account.balance:,.2f}",
                    parent=dialog
                )

                dialog.destroy()

            except ValueError as error:
                messagebox.showerror(
                    "Transaction Failed",
                    str(error),
                    parent=dialog
                )

            except OSError as error:
                messagebox.showerror(
                    "File Error",
                    str(error),
                    parent=dialog
                )

        ttk.Button(
            dialog,
            text="Submit",
            command=submit
        ).pack(pady=12)

        dialog.bind(
            "<Return>",
            lambda event: submit()
        )


# Part 5: Mini Statement and Account Summary

    def show_mini_statement(self, parent, account):
        window = tk.Toplevel(parent)
        window.title("Mini Statement")
        window.geometry("680x300")

        ttk.Label(
            window,
            text=f"Last 5 transactions — {account.username}",
            style="Heading.TLabel"
        ).pack(pady=12)

        frame = ttk.Frame(window, padding=10)
        frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            frame, orient="vertical"
        )

        listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            height=8
        )

        scrollbar.config(command=listbox.yview)

        listbox.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        latest = list(
            reversed(account.transactions[-5:])
        )

        if not latest:
            listbox.insert(
                tk.END, "No transactions yet."
            )

        for item in latest:
            listbox.insert(
                tk.END,
                f'{item["date"]} | {item["type"]:<12} | '
                f'₹{item["amount"]:,.2f} | '
                f'Balance ₹{item["balance"]:,.2f}'
            )

    def show_account_summary(self, parent, account):
        window = tk.Toplevel(parent)
        window.title("Account Summary")
        window.geometry("420x270")

        ttk.Label(
            window,
            text="Account Summary",
            style="Heading.TLabel"
        ).pack(pady=15)

        details = (
            f"Username: {account.username}\n\n"
            f"Account Number: {account.account_number}\n\n"
            f"Total Balance: ₹ {account.balance:,.2f}\n\n"
            f"Transaction Count: {len(account.transactions)}"
        )

        ttk.Label(
            window,
            text=details,
            justify="left"
        ).pack(padx=25, pady=10)



# Part 6: Interest Calculation, Delete Account and Main Program

    def show_interest(self, parent, account):
        interest = account.annual_interest()

        messagebox.showinfo(
            "Annual Interest Estimate",
            f"Annual rate: {ANNUAL_INTEREST_RATE:.0%}\n"
            f"Current balance: ₹ {account.balance:,.2f}\n"
            f"Estimated interest for one year: ₹ {interest:,.2f}\n"
            f"Balance after one year: "
            f"₹ {account.balance + interest:,.2f}",
            parent=parent
        )

    def delete_account(self, dashboard, account):
        confirmed = messagebox.askyesno(
            "Confirm Account Deletion",
            f"Are you sure you want to permanently "
            f"delete '{account.username}'?",
            parent=dashboard
        )

        if not confirmed:
            return

        try:
            self.bank.delete_account(account.username)
            dashboard.destroy()

            messagebox.showinfo(
                "Account Deleted",
                "Your account and its transaction records "
                "were deleted.",
                parent=self.root
            )

        except OSError as error:
            messagebox.showerror(
                "File Error",
                str(error),
                parent=dashboard
            )


# ------------ MAIN PROGRAM ------------

if __name__ == "__main__":
    root = tk.Tk()

    app = BankingApp(root)

    root.mainloop()

