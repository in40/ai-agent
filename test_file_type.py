#!/usr/bin/env python3
def get_file_type_from_filename(filename):
    if not filename:
        return 'unknown'
    filename_lower = filename.lower()
    if filename_lower.endswith('.pdf'):
        return 'pdf'
    elif filename_lower.endswith('.txt'):
        return 'txt'
    elif filename_lower.endswith('.json'):
        if 'chunk' in filename_lower:
            return 'chunks'
        elif 'metadata' in filename_lower:
            return 'metadata'
        else:
            return 'json'
    else:
        return 'other'

# Test with actual filenames
test_files = [
    'gost-r-56546-2015=edt2018_6d040aec.chunks.json',
    'r-1323565.1_881b0329.chunks.json',
    'r-1323565.1_9868b0c8.chunks.json',
    'gost-r-52633_8de4b632.chunks.json',
    'gost-r-59547-2021_c84a5a4d.chunks.json',
]

print("Testing file type detection:")
for f in test_files:
    print(f"  {f} -> {get_file_type_from_filename(f)}")
