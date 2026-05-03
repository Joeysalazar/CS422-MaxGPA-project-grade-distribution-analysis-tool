# MaxGPA - University of Oregon Grade Distribution Tool

CS 422 Software Methodologies – Spring 2026
Team: Adrianna, Joey, Reid, Abby

---

## How to Run MaxGPA (Step-by-Step)

Follow these steps exactly:

### 1. Download the project

* Download the project as a ZIP file from GitHub
* Extract (unzip) the folder to your Desktop

### 2. Install Python

* Go to: https://www.python.org/downloads/
* Download and install Python

### 3. Open the project in Terminal

- Open the extracted project folder
- Click in the address bar at the top of the folder
- Type:

```text
powershell
```

- Press **Enter**

![Example of opening PowerShell from the project folder](docs/images/Install-example.png)

This opens a terminal directly inside the project folder.

### 4. Install required packages

In the terminal, type:

```powershell
pip install -r requirements.txt
```

Press **Enter** and wait for it to finish.

### 5. Run the application

In the same terminal, type:

```powershell
python .\src\ui\app.py
```

Press **Enter**.

### 6. Open the website

The app should open automatically in your browser.

If it does not, open your browser and go to:

```text
http://127.0.0.1:5000
```

---

## What is MaxGPA?

MaxGPA is a web app that helps University of Oregon students choose courses and instructors strategically.

A student selects:

* a major
* a range of academic years

The app then shows:

* grade distributions for required courses
* instructor comparisons
* the best instructor for each course

---

## Supported Majors

* Computer Science
* Psychology
* Architecture

---

## Who is this for?

**Students**

* Compare instructors
* View grade distributions
* Plan schedules using historical grade data

**Administrators**

* Upload grade data
* Update degree plans
* Maintain reconciliation data

---

## Project Structure

```text
data/
  grades/
  degree_plans/

gradeAnalysis/
  student.py
  admin.py
  data_loader.py

src/ui/
  app.py
  templates/
  static/
```

---

## Notes

* Uses UO historical grade data from 2015–2025
* Required courses are defined in degree CSV files
* Flexible requirements such as CoreEd, electives, and choice groups are documented separately
* Reconciliation files help keep course naming consistent across datasets

---

## ✅ You’re Done!

You can now:

* select a major
* choose a year range
* view course grade data and instructor recommendations
