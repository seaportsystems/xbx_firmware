import boards
import os


HRD_DIR = "/sd/hrd"

def list_hrd_files():
    try:
        entries = os.listdir(HRD_DIR)
    except OSError as e:
        print(f"Error reading directory {HRD_DIR}: {e}")
        
    files = [f for f in sorted(entries) if os.listdir(HRD_DIR)]
    return files

def prompt_file_choice(files):
    for idx, fname in enumerate(files, start=1):
        print(f"{idx}. {fname}")
    while True:
        choice = input(f"Select file [1-{len(files)}] or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return None
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(files):
                return files[n-1]
        print("Invalid choice, try again.")

def view_file(path):
    print(f"\n=== Contents of {path} ===\n")
    try:
        with open(path, "r") as f:            
            for line in f:
                print(line.rstrip())
                
            f.seek(0)
            print(f"{len(f.readlines())} samples in file")
            
    except OSError as e:
        print(f"Failed to open {path}: {e}")
    print("\n=== End of file ===\n")

files = list_hrd_files()
if not files:
    print(f"No files found in {HRD_DIR}")

while True:
    fname = prompt_file_choice(files)
    if fname is None:
        print("Exiting.")
        break
    full_path = f"{HRD_DIR}/{fname}"
    
    view_file(full_path)