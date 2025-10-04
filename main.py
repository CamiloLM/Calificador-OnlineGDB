import os

import settings
from src.assignment import Assignment
from src.notes import Notes


def main():
    csv_paths = [
        os.path.join(settings.EXPORTS_DIR, f)
        for f in os.listdir(settings.EXPORTS_DIR)
        if f.endswith(".csv")
    ]

    assignments = [Assignment(path) for path in csv_paths]

    for a in assignments:
        a.grade_students()
        a.save_assignment(settings.GRADED_DIR)

    notes = Notes(settings.GRADED_DIR)
    notes.save_notes(settings.NOTES_FILE)


if __name__ == "__main__":
    main()
