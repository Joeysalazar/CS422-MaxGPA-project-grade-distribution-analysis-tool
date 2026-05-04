import csv

REQ_GRADE_FIELDS = ["TERM", "SUBJ"]

#get exact course num from row with flexible col naming
def get_course_number(row):
    return (
        row.get("NUM") or
        row.get("NUMB") or
        row.get("num") or
        ""
    ).strip()

#validate CSV headers 
def validate_headers(fieldnames):
    #checks headers and required fields
    if not fieldnames:
        return False, "No headers found."

    normalized = [str(f).strip().upper() for f in fieldnames]

    missing = [f for f in REQ_GRADE_FIELDS if f not in normalized]

    if missing:
        return False, f"Missing required columns: {missing}"

    return True, "Headers look valid."

#preview CSV file
def preview_csv(filepath):
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)

        valid, message = validate_headers(reader.fieldnames)
        print("\nHeader Check:", message)

        if not valid:
            return False

        for row in reader:
            if any(v not in ("", "*", None) for v in row.values()):
                print("\n--- Preview Row ---")
                for k, v in row.items():
                    print(f"{k}: {v}")
                return True

    print("No valid data rows found.")
    return False

#prompt user for confirmation before commiting changes
def confirm_load():
    while True:
        choice = input("\nProceed with loading this data? (y/n): ").strip().lower()

        if choice in ('y', 'n'):
            return choice == 'y'

        print("Please enter 'y' or 'n'.")

#load CSV into memory after validation
def load_csv(filepath):
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        if not rows:
            raise ValueError("CSV file is empty.")

        return rows