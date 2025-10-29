import os

files_to_remove = [
    "ADMIN_SETUP.md",
    "ADMIN_QUICK_GUIDE.md", 
    "SETUP_RU.md",
    "QUICK_START.md",
    "videodownloader.py",
    "setup_and_run.bat"
]

for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
        print(f"Removed: {file}")
    else:
        print(f"Not found: {file}")

print("Cleanup complete!")
