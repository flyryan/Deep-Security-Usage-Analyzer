"""
File Deduplication Script

This script removes duplicate files in a directory by comparing their SHA-256 hash values.

Usage:
    Run the script in the directory where you want to remove duplicates.
"""

import os
import hashlib

def hash_file(filepath):
    """Generate a SHA-256 hash for the content of the file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def remove_duplicates(directory):
    """Remove duplicate files in the specified directory."""
    hash_map = {}
    duplicates = []

    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_hash = hash_file(filepath)

            if file_hash in hash_map:
                duplicates.append(filepath)
            else:
                hash_map[file_hash] = filepath

    # Remove duplicates
    for duplicate in duplicates:
        print(f"Removing duplicate: {duplicate}")
        os.remove(duplicate)

if __name__ == "__main__":
    # Use current directory instead of user input
    current_directory = os.getcwd()
    remove_duplicates(current_directory)
    print("Duplicate files removed successfully.")