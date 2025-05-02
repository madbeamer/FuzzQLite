from typing import Set, Tuple

Location = Tuple[str, int]  # (function_name, line_number)

def read_gcov_coverage(c_file) -> Set[Location]:
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
