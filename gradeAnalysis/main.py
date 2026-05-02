from student import main as student_main
from admin import admin_menu

def main():
    print("Select role:")
    print("1. Student")
    print("2. Administrator")

    choice = input("Enter choice: ").strip()

    if choice == "1":
        student_main()
    elif choice == "2":
        admin_menu()
    else:
        print("Invalid selection.")

if __name__ == "__main__":
    main()