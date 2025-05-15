import subprocess
import re
import os
import shutil
from typing import Set, Tuple

def read_gcov_coverage_percentage() -> float:
    """
    Read the accumulative coverage percentage from gcov.
        
    Returns:
        Coverage percentage
    """
    # Run gcov command to get the accumulative coverage percentage
    cmd = ["gcov", "-o", "sqlite3-sqlite3", "sqlite3.c"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, cwd="/home/test/sqlite")
    
    # Extract the coverage percentage from the output
    output = result.stdout
    match = re.search(r"Lines executed:(\d+\.\d+)% of \d+", output)
    
    if match:
        coverage_percentage = float(match.group(1))
        return coverage_percentage
    else:
        return -1

def read_gcov_coverage(c_file) -> Set[Tuple[str, int]]:
    """
    Read only the newly executed lines from the current run.
    
    Args:
        c_file: The C file to get coverage for
    
    Returns:
        Set of tuples containing (c_file, line_number) for lines executed in this run
    """
    sqlite_dir = "/home/test/sqlite"
    
    # Create backup directory if it doesn't exist
    backup_dir = os.path.join(sqlite_dir, "gcov_data_backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Back up the .gcda file before any operations
    gcda_file = os.path.join(sqlite_dir, "sqlite3-sqlite3.gcda")
    backup_gcda_file = os.path.join(backup_dir, "sqlite3-sqlite3.gcda.backup")
    
    if os.path.exists(gcda_file):
        shutil.copy2(gcda_file, backup_gcda_file)
    else:
        # If no .gcda file exists yet, create an empty set and return
        return set()
    
    # Read the current .gcda file as binary data
    with open(gcda_file, 'rb') as f:
        current_gcda_data = f.read()
    
    # Check if we have a previous run's .gcda file to compare against
    prev_gcda_file = os.path.join(backup_dir, "sqlite3-sqlite3.gcda.prev")
    
    if os.path.exists(prev_gcda_file):
        # Make a temporary copy of the previous .gcda file
        temp_gcda = os.path.join(sqlite_dir, "sqlite3-sqlite3.gcda.temp")
        shutil.copy2(prev_gcda_file, temp_gcda)
        
        # Temporarily replace the current .gcda with the previous one
        shutil.move(temp_gcda, gcda_file)
        
        # Run gcov on the previous .gcda to get the previous coverage
        cmd = ["gcov", "-o", "sqlite3-sqlite3", "sqlite3.c"]
        subprocess.run(cmd, stdout=subprocess.PIPE, text=True, cwd=sqlite_dir)
        
        # Rename the resulting gcov file to avoid conflicts
        prev_gcov = os.path.join(sqlite_dir, "sqlite3.c.gcov")
        prev_gcov_renamed = os.path.join(sqlite_dir, "sqlite3.c.prev.gcov")
        if os.path.exists(prev_gcov):
            shutil.move(prev_gcov, prev_gcov_renamed)
        
        # Now restore the current .gcda file
        with open(gcda_file, 'wb') as f:
            f.write(current_gcda_data)
            
        # Run gcov on the current .gcda to get the current coverage
        subprocess.run(cmd, stdout=subprocess.PIPE, text=True, cwd=sqlite_dir)
        
        # We now have two .gcov files: the current one and the previous one
        # Use a simple script to find the difference between them
        if os.path.exists(prev_gcov_renamed) and os.path.exists(prev_gcov):
            # Create a shell command to efficiently find differences between files
            # This is much faster than parsing both files in Python
            diff_cmd = [
                "bash", "-c", 
                f"diff -u {prev_gcov_renamed} {prev_gcov} | grep '^+' | grep -v '^+++' | cut -d':' -f2 > {sqlite_dir}/diff_lines.txt"
            ]
            subprocess.run(diff_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=sqlite_dir)
            
            # Read the diff lines from the file
            diff_lines_file = os.path.join(sqlite_dir, "diff_lines.txt")
            incremental_coverage = set()
            
            if os.path.exists(diff_lines_file):
                with open(diff_lines_file) as f:
                    for line in f:
                        try:
                            line_number = int(line.strip())
                            incremental_coverage.add((c_file, line_number))
                        except ValueError:
                            continue
                
                # Clean up the temporary file
                os.remove(diff_lines_file)
            
            # Clean up the previous gcov file
            os.remove(prev_gcov_renamed)
    else:
        # If no previous run, all lines are new
        # Run gcov on the current .gcda
        cmd = ["gcov", "-o", "sqlite3-sqlite3", "sqlite3.c"]
        subprocess.run(cmd, stdout=subprocess.PIPE, text=True, cwd=sqlite_dir)
        
        # Read all covered lines from the gcov file
        gcov_file = os.path.join(sqlite_dir, "sqlite3.c.gcov")
        incremental_coverage = set()
        
        if os.path.exists(gcov_file):
            with open(gcov_file) as file:
                for line in file.readlines():
                    elems = line.split(':')
                    if len(elems) < 3:  # Skip malformed lines
                        continue
                    covered = elems[0].strip()
                    try:
                        line_number = int(elems[1].strip())
                    except ValueError:
                        continue  # Skip if line number is not an integer
                    
                    # Add all executed lines
                    if covered != '0' and not covered.startswith('#') and not covered.startswith('-') and not covered.startswith('='):
                        incremental_coverage.add((c_file, line_number))
    
    # Save the current .gcda for the next comparison
    shutil.copy2(gcda_file, prev_gcda_file)
    
    return incremental_coverage
