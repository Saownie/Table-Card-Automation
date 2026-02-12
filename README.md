# 🍽️ Royal Opera House - Table Card Automation Tool

A secure, GDPR-compliant web application designed to automate the generation of dining table cards for the Royal Opera House restaurant operations. This tool transforms raw reservation data (CSV) into formatted, print-ready Microsoft Word documents, streamlining the workflow for the Balconies, Paul Hamlyn Hall, and Crush Room teams.

## 🚀 Overview

Operational efficiency and data privacy are at the core of this project. Previously, creating table cards was a manual process prone to human error. This solution parses complex guest data—including dietary requirements and interval timings—and intelligently formats it into specific templates.

[**🚀 Launch Live Website**](https://saowns.pythonanywhere.com/login)

**Key Capabilities:**
* **Instant Generation:** Converts hundreds of reservations into printed cards in seconds.
* **Smart Categorization:** Automatically sorts items into Starters, Mains, Sides, Desserts, and Drinks.
* **Context Awareness:** Handles complex timing logic (Pre-Performance vs. Interval).
* **Business Logic:** Applies specific rules per restaurant (e.g., filtering water from "Crush" cards).

## 🛡️ Security & GDPR Compliance

This application follows a **"Privacy by Design"** architecture to ensure strict compliance with UK GDPR regulations regarding guest data.

### 1. Zero-Retention Architecture
The system acts as a transient processor. It does not store guest data.
* **Input Parsing:** CSV files are processed in memory and deleted immediately upon completion.
* **Output Delivery:** Generated Word documents are deleted from the server instantly after the download is handed off to the user.

### 2. "The Janitor" Protocol (Fail-Safe)
A secondary automated script (`janitor.py`) runs periodically to forcibly remove any temporary files older than 10 minutes, ensuring data hygiene even in the event of a server crash.

### 3. Access Control
* **Secure Login:** The application is gated behind a session-based authentication system.
* **Auto-Termination:** Sessions automatically time out after **5 minutes of inactivity** to prevent unauthorized access in shared office environments.

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **Web Framework:** Flask
* **Document Engine:** `docxtpl` (Jinja2 for Word), `docxcompose` (Document merging)
* **Data Processing:** `csv`, `pandas` (optional)
* **Hosting:** PythonAnywhere (WSGI)

## 📂 Project Structure

```text
├── app.py                 # Main Flask application entry point
├── card_processor.py      # Core logic for parsing CSVs and generating DOCX files
├── janitor.py             # Automated script for cleaning temp folders (GDPR)
├── templates/             # HTML templates for the web interface
│   ├── index.html
│   └── login.html
├── master_templates/      # Source Word templates (.docx)
│   ├── Balcony Cards.docx
│   ├── Crush Cards.docx
│   └── PHH Cards.docx
├── temp_generated/        # Transient folder for output files (auto-wiped)
├── temp_uploads/          # Transient folder for input files (auto-wiped)
└── requirements.txt       # Python dependencies
