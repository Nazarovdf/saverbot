import shutil
import os

temp_dir = "temp_downloads"

if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"Cleaned: {temp_dir}")
else:
    print(f"Not found: {temp_dir}")

# Recreate empty temp dir
os.makedirs(temp_dir, exist_ok=True)
print("Recreated empty temp_downloads/")
