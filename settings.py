from os import path

BASE_DIR = path.dirname(path.abspath(__file__))
EXPORTS_DIR = "exports"
GRADED_DIR = "graded"
NOTES_FILE = "notes.csv"
DUE_DATES_FILE = "due_dates.json"
DUE_DATES_PATH = path.join(BASE_DIR, DUE_DATES_FILE)
