import subprocess
import re
from typing import Set, Tuple

def read_gcov_coverage(c_file) -> Set[Tuple[str, int]]: # set of (c_file, line_number)
    gcov_file = c_file + ".gcov"
    coverage = set()
    with open(gcov_file) as file:
        for line in file.readlines():
            elems = line.split(':')
            covered = elems[0].strip()
            line_number = int(elems[1].strip())
            if covered.startswith('-') or covered.startswith('#'):
                continue
            coverage.add((c_file, line_number))
    return coverage

def read_gcov_coverage_percentage() -> float:
    """
    Read the coverage percentage from a file.
        
    Returns:
        Coverage percentage
    """
    # Run gcov command on the file at cwd=/home/test/sqlite
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
