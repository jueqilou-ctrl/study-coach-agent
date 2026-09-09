# Study Coach Agent

An AI study coach project built step by step with Python. The first version can upload a text-based PDF, extract its text, and preview individual pages.

## Current features

- Upload a PDF in the browser
- Extract text page by page
- Display the number of pages and characters
- Preview any page
- Detect PDFs that probably need OCR

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the virtual environment on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If you use Windows Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the app:

```bash
python -m streamlit run app.py
```

Your browser should open at `http://localhost:8501`.

## Upload this project to GitHub

### 1. Create an empty GitHub repository

On GitHub, select **New repository**, name it `study-coach-agent`, and do not add a README, `.gitignore`, or licence because this project already contains those files.

### 2. Configure Git once

Replace the example values with your own name and GitHub email:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

### 3. Create the first local commit

Run these commands from the project folder:

```bash
git init
git add .
git status
git commit -m "feat: add PDF text extraction prototype"
git branch -M main
```

Check `git status` before committing. Never upload `.env` or API keys.

### 4. Connect and push to GitHub

Copy the HTTPS URL from your new repository and replace the example URL:

```bash
git remote add origin https://github.com/YOUR_USERNAME/study-coach-agent.git
git push -u origin main
```

GitHub may ask you to sign in through the browser. A GitHub account password cannot be used as an HTTPS Git password; use the browser login flow or a personal access token if prompted.

### 5. Push later changes

```bash
git add .
git status
git commit -m "describe your change"
git push
```

## Planned development

1. Split extracted text into searchable chunks
2. Create embeddings and retrieve relevant course content
3. Add model API calls with structured output
4. Add quiz-generation and marking tools
5. Save weak topics and learning progress
6. Let the agent revise the study plan

