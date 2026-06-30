# Data Model

SQLite is the source of truth.

Excel files are used for:
- manual data entry
- bulk import
- export
- reports

## Initial Tables

### accounts
Stores checking, savings, credit card, loan, investment, and cash accounts.

### transactions
Stores income and expense transactions.

### categories
Stores spending and income categories.

### debts
Stores debts such as credit cards, car loans, student loans, and mortgages.

### assets
Stores assets such as cash, home value, vehicles, retirement accounts, and investments.

### budgets
Stores monthly budget targets by category.

### goals
Stores financial goals.

### ai_notes
Stores AI-generated observations and recommendations.

### import_batches
Tracks imported Excel or CSV files.

### audit_log
Tracks changes made inside the app.