# Steel Transaction System

**An operational transaction tracker for wholesale steel trading, built with Python, Streamlit, and SQL Server.**

This project is not an ERP or an accounting system. It gives sales staff and managers an up-to-date view of purchases, sales, and remaining stock without waiting for transactions to reach the accounting system.

> **Status:** V1.3 · Preparing for a parallel pilot. The application source is included, but it requires an existing SQL Server schema. End-to-end pilot acceptance is not yet documented.

## Why I built it

In the workflow this project was designed for, it could take about a week for a transaction to appear in the accounting system. In the meantime, the sales team relied on spreadsheets and paperwork to track purchases, partial sales, and remaining quantities.

I built this tool to capture that information once, at the point of entry, and make it available for operational reporting as soon as a transaction is saved. The goal is to reduce duplicate entry, manual calculations, and the errors that come with them—not to replace the accounting system. A later goal is to automate commission calculations from the captured transactions.

## What the current version does

- Records purchases and sales in a Persian, right-to-left interface with Jalali date input.
- Links **multiple partial sales to one purchase** and shows the remaining quantity. Each sale currently references just one purchase.
- Supports one or two quantity-and-price pairs per transaction and calculates totals.
- Shows the difference between the sale amount and its allocated purchase cost. This is a **spread, not net profit**.
- Requires a reason for corrections and saves before-and-after values alongside the update.
- Provides a linked sales report, an open-purchase view, and CSV export.

## A design decision: checking stock at save time

The remaining quantity shown in the form can become stale. If two operators open the same purchase, both might see enough stock before either saves.

To address that, the save path in [`app_v1.py`](app_v1.py) locks the purchase row, recalculates the sold quantity, and checks the available balance inside the same SQL Server transaction before writing the sale. Corrections also use SQL Server `rowversion` to reject stale updates rather than silently overwrite someone else's changes.

The locking logic is implemented. A two-operator test against a live SQL Server is still on the roadmap.

## Running the current source

The current package is **not a fresh-install demo**. It requires Python, Microsoft ODBC Driver 17 for SQL Server, and an existing database with the V4 base schema and the V1 migration applied. [`sql/migrate.sql`](sql/migrate.sql) updates that schema; it does not create the base tables.

If you already have a compatible development database, run the following in **Windows Command Prompt** from the repository root:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
set STEEL_SERVER=YOUR_SERVER\INSTANCE
set STEEL_DB=SteelTransaction_POC
python -m streamlit run app_v1.py
```

The database connection uses Windows integrated authentication. That does **not** authenticate individual application users: the current sidebar selection is not a login. Do not expose this version to the public internet.

## Roadmap

### Data entry and reporting

- [ ] Add quick search to purchase and sales lists.
- [ ] Show thousands separators while entering amounts.
- [ ] Display amounts in Persian words.
- [ ] Warn operators about possible duplicate invoices before saving.
- [ ] Show the full history of each transaction in one place.
- [ ] Automate commission calculations once the business rules are approved.

### Reliability and access

- [ ] Test simultaneous sales against the same purchase using two operator sessions.
- [ ] Add application error logging.
- [ ] Automate database backups and verify that they can be restored.
- [ ] Add a sign-in page with individual username and password accounts.
- [ ] Define user roles and permissions.
- [ ] Record sign-in and sign-out events.
- [ ] Restrict edits to older transactions.
- [ ] Serve the application over HTTPS.

### Transaction workflow

- [ ] Allocate a single sale across multiple purchases.
- [ ] Create pro forma invoices.
- [ ] Track transaction status and let managers approve or reject transactions.
- [ ] Void transactions without deleting their history.
- [ ] Record purchase and sales returns.
- [ ] Record service costs associated with transactions.

### Repository setup

- [ ] Add a database bootstrap script and synthetic sample data so the project can be tried without an existing company database.
