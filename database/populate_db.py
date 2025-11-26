import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()


def main():
    print("How do you want to populate the database?")
    print("1) Using CSV files")
    print("2) Using example data")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        print("Running pop_with_csv.py...\n")
        subprocess.run(["python", "pop_with_csv.py"], check=True, cwd=BASE_DIR)

    elif choice == "2":
        print("Running pop_with_example.py...\n")
        subprocess.run(["python", "pop_with_example.py"], check=True, cwd=BASE_DIR)

    else:
        print("Invalid option. Exiting.")


if __name__ == "__main__":
    main()
