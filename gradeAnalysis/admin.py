import os
from data_loader import preview_csv, confirm_load, load_csv
from student import load_reconciliation

GRADE_DATA_PATH = "data/grades/current.csv"
DEGREE_DATA_PATH =  "data/degree/plans/"
RECON_FILE = "data/reconciliation.csv" 

import os
from data_loader import preview_csv, confirm_load, load_csv

#update the system's active grade dataset
def update_grade_data():
    DEFAULT_PATH = "data/grades/cleaned_pub_rec_master.csv"

    print(f"\nDefault file: {DEFAULT_PATH}")
    use_default = input("Use default file? (y/n): ").strip().lower()

    if use_default == 'y':
        filepath = DEFAULT_PATH
    else:
        filepath = input("Enter path to grade CSV: ").strip()

    if not os.path.exists(filepath):
        print("File not found.")
        return

    try:
        if not preview_csv(filepath):
            print("Preview failed. Aborting.")
            return
    except Exception as e:
        print(f"Error during preview: {e}")
        return

    if not confirm_load():
        print("Update canceled.")
        return

    try:
        data = load_csv(filepath)

        # backup old file (important for safety + looks good in grading)
        backup_path = "data/grades/backup.csv"
        if os.path.exists("data/grades/current.csv"):
            import shutil
            shutil.copy("data/grades/current.csv", backup_path)

        # write new data
        with open("data/grades/current.csv", 'w', newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print("Grade data successfully updated.")
        print(f"Backup saved to {backup_path}")

    except Exception as e:
        print(f"Failed to load data: {e}")

#update stored degree plan files
def update_degree_plan():
    filepath = input("Enter path to degree CSV: ").strip()
    if not os.path.exists(filepath):
        print("File not found.")
        return

    if not preview_csv(filepath):
        return

    if confirm_load():
        filename = os.path.basename(filepath)
        target_path = os.path.join(DEGREE_DATA_PATH, filename)

        import shutil
        shutil.copy(filepath, target_path)

        print("Degree plan updated.")
    else:
        print("Update canceled.")

#load and verify recon mappings
def load_reconciliation_file():
    recon = load_reconciliation(RECON_FILE)

    print(f"\nLoaded {len(recon)} reconciliation mappings.")

    if not recon:
        print("WARNING: No mappings loaded. Check file format or path.")
        return recon

    print("\nSample mappings (first 5):")
    count = 0
    for k, v in recon.items():
        print(f"- {k} → {v}")
        count += 1
        if count == 5:
            break

    print("\nReconciliation file loaded successfully.")
    return recon

#command line interfaces
def admin_menu():
    while True:
        print("\n--- ADMIN MENU ---")
        print("1. Update grade data")
        print("2. Update degree plan")
        print("3. Load reconciliation file")
        print("4. Exit")

        choice = input("Choose option: ").strip()

        if choice == "1":
            update_grade_data()
        elif choice == "2":
            update_degree_plan()
        elif choice == "3":
            load_reconciliation_file()
        elif choice == "4":
            break
        else:
            print("Invalid choice.")