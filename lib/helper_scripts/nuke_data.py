import boards
import os


DIR = "/sd/sample_data"

sample_files = os.listdir(DIR)

for file in sample_files:
    print(f"Deleting: {file}")
    os.remove(f"{DIR}/{file}")