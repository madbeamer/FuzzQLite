class Outcome:
    PASS = "PASS"                        # Executed successfully with same result as reference
    REFERENCE_ERROR = "REFERENCE_ERROR"  # Target executed successfully but reference SQLite crashed
    CRASH = "CRASH"                      # Target SQLite crashed, reference didn't
    LOGIC_BUG = "LOGIC_BUG"              # Different result between target and reference (both succeeded)
    INVALID_QUERY = "INVALID_QUERY"      # Both target and reference SQLite crashed
    