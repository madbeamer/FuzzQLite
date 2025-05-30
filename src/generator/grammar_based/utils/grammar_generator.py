import json
import re

def parse_grammar_string(grammar_string):
    """
    Parse a grammar string and convert it to a dictionary with helper functions
    for alternative expressions inside parentheses. The input grammar string is
    in ANTLR v4 format (see https://github.com/antlr/grammars-v4/tree/master/sql/sqlite).
    
    Args:
        grammar_string: String containing the grammar rules
        
    Returns:
        Dictionary representation of the grammar with all values as lists
    """
    # Initialize variables
    grammar = {}
    helper_counter = 1
    rules_map = {}  # To track all rule names for later conversion
    
    # Split into rules - careful with ;
    rules = []
    current_rule = ""
    in_single_quotes = False
    
    for char in grammar_string:
        current_rule += char
        
        if char == "'":
            in_single_quotes = not in_single_quotes
        
        if char == ';' and not in_single_quotes:
            rules.append(current_rule.strip())
            current_rule = ""
    
    # Handle any remaining content
    if current_rule.strip():
        rules.append(current_rule.strip())
    
    # First pass: collect all rule names for later reference
    for rule_text in rules:
        rule_text = rule_text.strip()
        if not rule_text or ':' not in rule_text:
            continue
        
        rule_name = rule_text.split(':', 1)[0].strip()
        rules_map[rule_name] = f"<{rule_name}>"
    
    # Second pass: process rules
    for rule_text in rules:
        rule_text = rule_text.strip()
        if not rule_text:
            continue
            
        # Extract rule name and body
        parts = rule_text.split(':', 1)
        if len(parts) != 2:
            continue
            
        rule_name = parts[0].strip()
        rule_body = parts[1].strip()
        
        # Remove trailing semicolon if present
        if rule_body.endswith(';'):
            rule_body = rule_body[:-1].strip()
        
        # Check if this is a simple token definition (like SCOL: ';')
        if rule_body.startswith("'") and rule_body.endswith("'"):
            # Extract the actual character without quotes
            token_value = rule_body[1:-1]
            grammar[f"<{rule_name}>"] = [token_value]  # Put in list
            continue
        
        # Process rule body with the current global helper counter
        result_dict = process_rule(rule_name, rule_body, helper_counter, rules_map)
        
        # Update grammar dictionary
        grammar.update(result_dict)
        
        # Update helper_counter to ensure unique helper names across all rules
        new_helpers = [k for k in result_dict.keys() if k.startswith('<h') and k[2:-1].isdigit()]
        if new_helpers:
            helper_counter = max([int(k[2:-1]) for k in new_helpers]) + 1
    
    # Convert all string values to lists, handling special cases
    special_tokens = ["<PIPE>", "<PIPE2>"]
    
    for key, value in grammar.items():
        if isinstance(value, str):
            if '|' in value and key not in special_tokens:
                # Split by | and clean each part
                parts = [part.strip() for part in value.split('|')]
                grammar[key] = parts
            else:
                # Put single value in a list
                grammar[key] = [value]
    
    return grammar

def process_rule(rule_name, rule_body, helper_counter, rules_map):
    """Process a rule and extract alternatives into helper functions."""
    result = {}
    helpers = {}
    
    def find_closing_paren(text, start):
        """Find the position of the matching closing parenthesis."""
        count = 1
        i = start + 1
        while i < len(text) and count > 0:
            if text[i] == '(' and not is_in_quotes(text, i):
                count += 1
            elif text[i] == ')' and not is_in_quotes(text, i):
                count -= 1
            i += 1
        return i - 1 if count == 0 else -1
    
    def is_in_quotes(text, pos):
        """Check if the character at position pos is inside quotes."""
        # Count single quotes before this position
        single_quotes = text[:pos].count("'")
        # If odd number of quotes, we're inside quotes
        return single_quotes % 2 == 1
    
    def clean_text(text):
        """Clean up whitespace and newlines in text."""
        # Replace consecutive whitespace with a single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def wrap_rule_references(text):
        """
        Wrap rule references in angle brackets.
        This needs to be done carefully to avoid wrapping non-rule words.
        """
        for rule_name, wrapped_name in rules_map.items():
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(rule_name) + r'\b'
            text = re.sub(pattern, wrapped_name, text)
        return text
    
    def process_alternatives(text, current_counter):
        """Recursively process text to extract alternatives."""
        processed = ""
        i = 0
        local_counter = current_counter
        
        while i < len(text):
            # Handle quoted content as a unit
            if text[i] == "'":
                quote_end = text.find("'", i + 1)
                if quote_end == -1:
                    processed += text[i]
                    i += 1
                else:
                    # Replace quoted content with just the character itself
                    char_inside = text[i+1:quote_end]
                    processed += char_inside
                    i = quote_end + 1
                continue
                
            if text[i] == '(' and not is_in_quotes(text, i):
                # Find matching closing parenthesis
                closing = find_closing_paren(text, i)
                if closing == -1:
                    processed += text[i]
                    i += 1
                    continue
                
                # Extract content inside parentheses
                content = text[i+1:closing]
                
                # Check for quantifier
                quantifier = ""
                next_pos = closing + 1
                if next_pos < len(text) and text[next_pos] in "?*+":
                    quantifier = text[next_pos]
                    next_pos += 1
                
                # Process content if it contains alternatives
                if '|' in content and not is_in_quotes(content, content.find('|')):
                    # Recursively process the content first
                    inner_processed, local_counter = process_alternatives(content, local_counter)
                    
                    # Create a helper for this alternative
                    helper_name = f"h{local_counter}"
                    wrapped_helper = f"<{helper_name}>"
                    helpers[wrapped_helper] = wrap_rule_references(clean_text(inner_processed))
                    local_counter += 1
                    
                    # Add helper reference to result
                    processed += wrapped_helper + quantifier
                else:
                    # Keep original parentheses if no alternatives
                    processed += '(' + clean_text(content) + ')' + quantifier
                
                i = next_pos
            else:
                processed += text[i]
                i += 1
        
        return processed, local_counter
    
    # Process the rule body
    processed_body, final_counter = process_alternatives(rule_body, helper_counter)
    
    # Wrap rule references and add to result
    wrapped_rule_name = f"<{rule_name}>"
    result[wrapped_rule_name] = wrap_rule_references(clean_text(processed_body))
    
    # Update helpers with wrapped rule references
    for helper_name, helper_body in helpers.items():
        result[helper_name] = helper_body
    
    return result

def save_grammar_to_file(grammar_dict, output_file):
    """
    Save a grammar dictionary to a JSON file.
    
    Args:
        grammar_dict: Dictionary containing the parsed grammar
        output_file: Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(grammar_dict, f, indent=2)
    
    print(f"Successfully wrote parsed grammar to {output_file}")

def main():
    file_content = """
    parse
        : (sql_stmt_list)* EOF
    ;

    sql_stmt_list
        : SCOL* sql_stmt (SCOL+ sql_stmt)* SCOL*
    ;

    sql_stmt
        : (EXPLAIN_ (QUERY_ PLAN_)?)? (
            alter_table_stmt
            | analyze_stmt
            | attach_stmt
            | begin_stmt
            | commit_stmt
            | create_index_stmt
            | create_table_stmt
            | create_trigger_stmt
            | create_view_stmt
            | create_virtual_table_stmt
            | delete_stmt
            | delete_stmt_limited
            | detach_stmt
            | drop_stmt
            | insert_stmt
            | pragma_stmt
            | reindex_stmt
            | release_stmt
            | rollback_stmt
            | savepoint_stmt
            | select_stmt
            | update_stmt
            | update_stmt_limited
            | vacuum_stmt
        )
    ;

    alter_table_stmt
        : ALTER_ TABLE_ (schema_name DOT)? table_name (
            RENAME_ (
                TO_ new_table_name = table_name
                | COLUMN_? old_column_name = column_name TO_ new_column_name = column_name
            )
            | ADD_ COLUMN_? column_def
            | DROP_ COLUMN_? column_name
        )
    ;

    analyze_stmt
        : ANALYZE_ (schema_name | (schema_name DOT)? table_or_index_name)?
    ;

    attach_stmt
        : ATTACH_ DATABASE_? expr AS_ schema_name
    ;

    begin_stmt
        : BEGIN_ (DEFERRED_ | IMMEDIATE_ | EXCLUSIVE_)? (TRANSACTION_ transaction_name?)?
    ;

    commit_stmt
        : (COMMIT_ | END_) TRANSACTION_?
    ;

    rollback_stmt
        : ROLLBACK_ TRANSACTION_? (TO_ SAVEPOINT_? savepoint_name)?
    ;

    savepoint_stmt
        : SAVEPOINT_ savepoint_name
    ;

    release_stmt
        : RELEASE_ SAVEPOINT_? savepoint_name
    ;

    create_index_stmt
        : CREATE_ UNIQUE_? INDEX_ (IF_ NOT_ EXISTS_)? (schema_name DOT)? index_name ON_ table_name OPEN_PAR indexed_column (
            COMMA indexed_column
        )* CLOSE_PAR (WHERE_ expr)?
    ;

    indexed_column
        : (column_name | expr) (COLLATE_ collation_name)? asc_desc?
    ;

    create_table_stmt
        : CREATE_ (TEMP_ | TEMPORARY_)? TABLE_ (IF_ NOT_ EXISTS_)? (schema_name DOT)? table_name (
            OPEN_PAR column_def (COMMA column_def)*? (COMMA table_constraint)* CLOSE_PAR (
                WITHOUT_ row_ROW_ID = IDENTIFIER
            )?
            | AS_ select_stmt
        )
    ;

    column_def
        : column_name type_name? column_constraint*
    ;

    type_name
        : name+? (
            OPEN_PAR signed_number CLOSE_PAR
            | OPEN_PAR signed_number COMMA signed_number CLOSE_PAR
        )?
    ;

    column_constraint
        : (CONSTRAINT_ name)? (
            (PRIMARY_ KEY_ asc_desc? conflict_clause? AUTOINCREMENT_?)
            | (NOT_? NULL_ | UNIQUE_) conflict_clause?
            | CHECK_ OPEN_PAR expr CLOSE_PAR
            | DEFAULT_ (signed_number | literal_value | OPEN_PAR expr CLOSE_PAR)
            | COLLATE_ collation_name
            | foreign_key_clause
            | (GENERATED_ ALWAYS_)? AS_ OPEN_PAR expr CLOSE_PAR (STORED_ | VIRTUAL_)?
        )
    ;

    signed_number
        : (PLUS | MINUS)? NUMERIC_LITERAL
    ;

    table_constraint
        : (CONSTRAINT_ name)? (
            (PRIMARY_ KEY_ | UNIQUE_) OPEN_PAR indexed_column (COMMA indexed_column)* CLOSE_PAR conflict_clause?
            | CHECK_ OPEN_PAR expr CLOSE_PAR
            | FOREIGN_ KEY_ OPEN_PAR column_name (COMMA column_name)* CLOSE_PAR foreign_key_clause
        )
    ;

    foreign_key_clause
        : REFERENCES_ foreign_table (OPEN_PAR column_name (COMMA column_name)* CLOSE_PAR)? (
            ON_ (DELETE_ | UPDATE_) (
                SET_ (NULL_ | DEFAULT_)
                | CASCADE_
                | RESTRICT_
                | NO_ ACTION_
            )
            | MATCH_ name
        )* (NOT_? DEFERRABLE_ (INITIALLY_ (DEFERRED_ | IMMEDIATE_))?)?
    ;

    conflict_clause
        : ON_ CONFLICT_ (ROLLBACK_ | ABORT_ | FAIL_ | IGNORE_ | REPLACE_)
    ;

    create_trigger_stmt
        : CREATE_ (TEMP_ | TEMPORARY_)? TRIGGER_ (IF_ NOT_ EXISTS_)? (schema_name DOT)? trigger_name (
            BEFORE_
            | AFTER_
            | INSTEAD_ OF_
        )? (DELETE_ | INSERT_ | UPDATE_ (OF_ column_name ( COMMA column_name)*)?) ON_ table_name (
            FOR_ EACH_ ROW_
        )? (WHEN_ expr)? BEGIN_ (
            (update_stmt | insert_stmt | delete_stmt | select_stmt) SCOL
        )+ END_
    ;

    create_view_stmt
        : CREATE_ (TEMP_ | TEMPORARY_)? VIEW_ (IF_ NOT_ EXISTS_)? (schema_name DOT)? view_name (
            OPEN_PAR column_name (COMMA column_name)* CLOSE_PAR
        )? AS_ select_stmt
    ;

    create_virtual_table_stmt
        : CREATE_ VIRTUAL_ TABLE_ (IF_ NOT_ EXISTS_)? (schema_name DOT)? table_name USING_ module_name (
            OPEN_PAR module_argument (COMMA module_argument)* CLOSE_PAR
        )?
    ;

    with_clause
        : WITH_ RECURSIVE_? cte_table_name AS_ OPEN_PAR select_stmt CLOSE_PAR (
            COMMA cte_table_name AS_ OPEN_PAR select_stmt CLOSE_PAR
        )*
    ;

    cte_table_name
        : table_name (OPEN_PAR column_name ( COMMA column_name)* CLOSE_PAR)?
    ;

    recursive_cte
        : cte_table_name AS_ OPEN_PAR initial_select UNION_ ALL_? recursive_select CLOSE_PAR
    ;

    common_table_expression
        : table_name (OPEN_PAR column_name ( COMMA column_name)* CLOSE_PAR)? AS_ OPEN_PAR select_stmt CLOSE_PAR
    ;

    delete_stmt
        : with_clause? DELETE_ FROM_ qualified_table_name (WHERE_ expr)? returning_clause?
    ;

    delete_stmt_limited
        : with_clause? DELETE_ FROM_ qualified_table_name (WHERE_ expr)? returning_clause? (
            order_by_stmt? limit_stmt
        )?
    ;

    detach_stmt
        : DETACH_ DATABASE_? schema_name
    ;

    drop_stmt
        : DROP_ object = (INDEX_ | TABLE_ | TRIGGER_ | VIEW_) (IF_ EXISTS_)? (
            schema_name DOT
        )? any_name
    ;

    expr
        : literal_value
        | BIND_PARAMETER
        | ((schema_name DOT)? table_name DOT)? column_name
        | unary_operator expr
        | expr PIPE2 expr
        | expr ( STAR | DIV | MOD) expr
        | expr ( PLUS | MINUS) expr
        | expr ( LT2 | GT2 | AMP | PIPE) expr
        | expr ( LT | LT_EQ | GT | GT_EQ) expr
        | expr (
            ASSIGN
            | EQ
            | NOT_EQ1
            | NOT_EQ2
            | IS_
            | IS_ NOT_
            | IS_ NOT_? DISTINCT_ FROM_
            | IN_
            | LIKE_
            | GLOB_
            | MATCH_
            | REGEXP_
        ) expr
        | expr AND_ expr
        | expr OR_ expr
        | function_name OPEN_PAR ((DISTINCT_? expr ( COMMA expr)*) | STAR)? CLOSE_PAR filter_clause? over_clause?
        | OPEN_PAR expr (COMMA expr)* CLOSE_PAR
        | CAST_ OPEN_PAR expr AS_ type_name CLOSE_PAR
        | expr COLLATE_ collation_name
        | expr NOT_? (LIKE_ | GLOB_ | REGEXP_ | MATCH_) expr (ESCAPE_ expr)?
        | expr ( ISNULL_ | NOTNULL_ | NOT_ NULL_)
        | expr IS_ NOT_? expr
        | expr NOT_? BETWEEN_ expr AND_ expr
        | expr NOT_? IN_ (
            OPEN_PAR (select_stmt | expr ( COMMA expr)*)? CLOSE_PAR
            | ( schema_name DOT)? table_name
            | (schema_name DOT)? table_function_name OPEN_PAR (expr (COMMA expr)*)? CLOSE_PAR
        )
        | ((NOT_)? EXISTS_)? OPEN_PAR select_stmt CLOSE_PAR
        | CASE_ expr? (WHEN_ expr THEN_ expr)+ (ELSE_ expr)? END_
        | raise_function
    ;

    raise_function
        : RAISE_ OPEN_PAR (IGNORE_ | (ROLLBACK_ | ABORT_ | FAIL_) COMMA error_message) CLOSE_PAR
    ;

    literal_value
        : NUMERIC_LITERAL
        | STRING_LITERAL
        | BLOB_LITERAL
        | NULL_
        | TRUE_
        | FALSE_
        | CURRENT_TIME_
        | CURRENT_DATE_
        | CURRENT_TIMESTAMP_
    ;

    value_row
        : OPEN_PAR expr (COMMA expr)* CLOSE_PAR
    ;

    values_clause
        : VALUES_ value_row (COMMA value_row)*
    ;

    insert_stmt
        : with_clause? (
            INSERT_
            | REPLACE_
            | INSERT_ OR_ ( REPLACE_ | ROLLBACK_ | ABORT_ | FAIL_ | IGNORE_)
        ) INTO_ (schema_name DOT)? table_name (AS_ table_alias)? (
            OPEN_PAR column_name ( COMMA column_name)* CLOSE_PAR
        )? (( ( values_clause | select_stmt) upsert_clause?) | DEFAULT_ VALUES_) returning_clause?
    ;

    returning_clause
        : RETURNING_ result_column (COMMA result_column)*
    ;

    upsert_clause
        : ON_ CONFLICT_ (
            OPEN_PAR indexed_column (COMMA indexed_column)* CLOSE_PAR (WHERE_ expr)?
        )? DO_ (
            NOTHING_
            | UPDATE_ SET_ (
                (column_name | column_name_list) ASSIGN expr (
                    COMMA (column_name | column_name_list) ASSIGN expr
                )* (WHERE_ expr)?
            )
        )
    ;

    pragma_stmt
        : PRAGMA_ (schema_name DOT)? pragma_name (
            ASSIGN pragma_value
            | OPEN_PAR pragma_value CLOSE_PAR
        )?
    ;

    pragma_value
        : signed_number
        | name
        | STRING_LITERAL
    ;

    reindex_stmt
        : REINDEX_ (collation_name | (schema_name DOT)? (table_name | index_name))?
    ;

    select_stmt
        : common_table_stmt? select_core (compound_operator select_core)* order_by_stmt? limit_stmt?
    ;

    join_clause
        : table_or_subquery (join_operator table_or_subquery join_constraint?)*
    ;

    select_core
        : (
            SELECT_ (DISTINCT_ | ALL_)? result_column (COMMA result_column)* (
                FROM_ (table_or_subquery (COMMA table_or_subquery)* | join_clause)
            )? (WHERE_ whereExpr = expr)? (
                GROUP_ BY_ groupByExpr += expr (COMMA groupByExpr += expr)* (
                    HAVING_ havingExpr = expr
                )?
            )? (WINDOW_ window_name AS_ window_defn ( COMMA window_name AS_ window_defn)*)?
        )
        | values_clause
    ;

    factored_select_stmt
        : select_stmt
    ;

    simple_select_stmt
        : common_table_stmt? select_core order_by_stmt? limit_stmt?
    ;

    compound_select_stmt
        : common_table_stmt? select_core (
            (UNION_ ALL_? | INTERSECT_ | EXCEPT_) select_core
        )+ order_by_stmt? limit_stmt?
    ;

    table_or_subquery
        : (
            (schema_name DOT)? table_name (AS_? table_alias)? (
                INDEXED_ BY_ index_name
                | NOT_ INDEXED_
            )?
        )
        | (schema_name DOT)? table_function_name OPEN_PAR expr (COMMA expr)* CLOSE_PAR (
            AS_? table_alias
        )?
        | OPEN_PAR (table_or_subquery (COMMA table_or_subquery)* | join_clause) CLOSE_PAR
        | OPEN_PAR select_stmt CLOSE_PAR (AS_? table_alias)?
    ;

    result_column
        : STAR
        | table_name DOT STAR
        | expr ( AS_? column_alias)?
    ;

    join_operator
        : COMMA
        | NATURAL_? ((LEFT_ | RIGHT_ | FULL_) OUTER_? | INNER_ | CROSS_)? JOIN_
    ;

    join_constraint
        : ON_ expr
        | USING_ OPEN_PAR column_name ( COMMA column_name)* CLOSE_PAR
    ;

    compound_operator
        : UNION_ ALL_?
        | INTERSECT_
        | EXCEPT_
    ;

    update_stmt
        : with_clause? UPDATE_ (OR_ (ROLLBACK_ | ABORT_ | REPLACE_ | FAIL_ | IGNORE_))? qualified_table_name SET_ (
            column_name
            | column_name_list
        ) ASSIGN expr (COMMA (column_name | column_name_list) ASSIGN expr)* (
            FROM_ (table_or_subquery (COMMA table_or_subquery)* | join_clause)
        )? (WHERE_ expr)? returning_clause?
    ;

    column_name_list
        : OPEN_PAR column_name (COMMA column_name)* CLOSE_PAR
    ;

    update_stmt_limited
        : with_clause? UPDATE_ (OR_ (ROLLBACK_ | ABORT_ | REPLACE_ | FAIL_ | IGNORE_))? qualified_table_name SET_ (
            column_name
            | column_name_list
        ) ASSIGN expr (COMMA (column_name | column_name_list) ASSIGN expr)* (WHERE_ expr)? returning_clause? (
            order_by_stmt? limit_stmt
        )?
    ;

    qualified_table_name
        : (schema_name DOT)? table_name (AS_ alias)? (
            INDEXED_ BY_ index_name
            | NOT_ INDEXED_
        )?
    ;

    vacuum_stmt
        : VACUUM_ schema_name? (INTO_ filename)?
    ;

    filter_clause
        : FILTER_ OPEN_PAR WHERE_ expr CLOSE_PAR
    ;

    window_defn
        : OPEN_PAR base_window_name? (PARTITION_ BY_ expr (COMMA expr)*)? (
            ORDER_ BY_ ordering_term (COMMA ordering_term)*
        ) frame_spec? CLOSE_PAR
    ;

    over_clause
        : OVER_ (
            window_name
            | OPEN_PAR base_window_name? (PARTITION_ BY_ expr (COMMA expr)*)? (
                ORDER_ BY_ ordering_term (COMMA ordering_term)*
            )? frame_spec? CLOSE_PAR
        )
    ;

    frame_spec
        : frame_clause (EXCLUDE_ ( NO_ OTHERS_ | CURRENT_ ROW_ | GROUP_ | TIES_))?
    ;

    frame_clause
        : (RANGE_ | ROWS_ | GROUPS_) (
            frame_single
            | BETWEEN_ frame_left AND_ frame_right
        )
    ;

    simple_function_invocation
        : simple_func OPEN_PAR (expr (COMMA expr)* | STAR) CLOSE_PAR
    ;

    aggregate_function_invocation
        : aggregate_func OPEN_PAR (DISTINCT_? expr (COMMA expr)* | STAR)? CLOSE_PAR filter_clause?
    ;

    window_function_invocation
        : window_function OPEN_PAR (expr (COMMA expr)* | STAR)? CLOSE_PAR filter_clause? OVER_ (
            window_defn
            | window_name
        )
    ;

    common_table_stmt
        : WITH_ RECURSIVE_? common_table_expression (COMMA common_table_expression)*
    ;

    order_by_stmt
        : ORDER_ BY_ ordering_term (COMMA ordering_term)*
    ;

    limit_stmt
        : LIMIT_ expr ((OFFSET_ | COMMA) expr)?
    ;

    ordering_term
        : expr (COLLATE_ collation_name)? asc_desc? (NULLS_ (FIRST_ | LAST_))?
    ;

    asc_desc
        : ASC_
        | DESC_
    ;

    frame_left
        : expr PRECEDING_
        | expr FOLLOWING_
        | CURRENT_ ROW_
        | UNBOUNDED_ PRECEDING_
    ;

    frame_right
        : expr PRECEDING_
        | expr FOLLOWING_
        | CURRENT_ ROW_
        | UNBOUNDED_ FOLLOWING_
    ;

    frame_single
        : expr PRECEDING_
        | UNBOUNDED_ PRECEDING_
        | CURRENT_ ROW_
    ;

    window_function
        : (FIRST_VALUE_ | LAST_VALUE_) OPEN_PAR expr CLOSE_PAR OVER_ OPEN_PAR partition_by? order_by_expr_asc_desc frame_clause?
            CLOSE_PAR
        | (CUME_DIST_ | PERCENT_RANK_) OPEN_PAR CLOSE_PAR OVER_ OPEN_PAR partition_by? order_by_expr? CLOSE_PAR
        | (DENSE_RANK_ | RANK_ | ROW_NUMBER_) OPEN_PAR CLOSE_PAR OVER_ OPEN_PAR partition_by? order_by_expr_asc_desc CLOSE_PAR
        | (LAG_ | LEAD_) OPEN_PAR expr offset? default_value? CLOSE_PAR OVER_ OPEN_PAR partition_by? order_by_expr_asc_desc CLOSE_PAR
        | NTH_VALUE_ OPEN_PAR expr COMMA signed_number CLOSE_PAR OVER_ OPEN_PAR partition_by? order_by_expr_asc_desc frame_clause?
            CLOSE_PAR
        | NTILE_ OPEN_PAR expr CLOSE_PAR OVER_ OPEN_PAR partition_by? order_by_expr_asc_desc CLOSE_PAR
    ;

    offset
        : COMMA signed_number
    ;

    default_value
        : COMMA signed_number
    ;

    partition_by
        : PARTITION_ BY_ expr+
    ;

    order_by_expr
        : ORDER_ BY_ expr+
    ;

    order_by_expr_asc_desc
        : ORDER_ BY_ expr_asc_desc
    ;

    expr_asc_desc
        : expr asc_desc? (COMMA expr asc_desc?)*
    ;

    initial_select
        : select_stmt
    ;

    recursive_select
        : select_stmt
    ;

    unary_operator
        : MINUS
        | PLUS
        | TILDE
        | NOT_
    ;

    error_message
        : STRING_LITERAL
    ;

    module_argument
        :
        expr
        | column_def
    ;

    column_alias
        : IDENTIFIER
        | STRING_LITERAL
    ;

    keyword
        : ABORT_
        | ACTION_
        | ADD_
        | AFTER_
        | ALL_
        | ALTER_
        | ANALYZE_
        | AND_
        | AS_
        | ASC_
        | ATTACH_
        | AUTOINCREMENT_
        | BEFORE_
        | BEGIN_
        | BETWEEN_
        | BY_
        | CASCADE_
        | CASE_
        | CAST_
        | CHECK_
        | COLLATE_
        | COLUMN_
        | COMMIT_
        | CONFLICT_
        | CONSTRAINT_
        | CREATE_
        | CROSS_
        | CURRENT_DATE_
        | CURRENT_TIME_
        | CURRENT_TIMESTAMP_
        | DATABASE_
        | DEFAULT_
        | DEFERRABLE_
        | DEFERRED_
        | DELETE_
        | DESC_
        | DETACH_
        | DISTINCT_
        | DROP_
        | EACH_
        | ELSE_
        | END_
        | ESCAPE_
        | EXCEPT_
        | EXCLUSIVE_
        | EXISTS_
        | EXPLAIN_
        | FAIL_
        | FOR_
        | FOREIGN_
        | FROM_
        | FULL_
        | GLOB_
        | GROUP_
        | HAVING_
        | IF_
        | IGNORE_
        | IMMEDIATE_
        | IN_
        | INDEX_
        | INDEXED_
        | INITIALLY_
        | INNER_
        | INSERT_
        | INSTEAD_
        | INTERSECT_
        | INTO_
        | IS_
        | ISNULL_
        | JOIN_
        | KEY_
        | LEFT_
        | LIKE_
        | LIMIT_
        | MATCH_
        | NATURAL_
        | NO_
        | NOT_
        | NOTNULL_
        | NULL_
        | OF_
        | OFFSET_
        | ON_
        | OR_
        | ORDER_
        | OUTER_
        | PLAN_
        | PRAGMA_
        | PRIMARY_
        | QUERY_
        | RAISE_
        | RECURSIVE_
        | REFERENCES_
        | REGEXP_
        | REINDEX_
        | RELEASE_
        | RENAME_
        | REPLACE_
        | RESTRICT_
        | RIGHT_
        | ROLLBACK_
        | ROW_
        | ROWS_
        | SAVEPOINT_
        | SELECT_
        | SET_
        | TABLE_
        | TEMP_
        | TEMPORARY_
        | THEN_
        | TO_
        | TRANSACTION_
        | TRIGGER_
        | UNION_
        | UNIQUE_
        | UPDATE_
        | USING_
        | VACUUM_
        | VALUES_
        | VIEW_
        | VIRTUAL_
        | WHEN_
        | WHERE_
        | WITH_
        | WITHOUT_
        | FIRST_VALUE_
        | OVER_
        | PARTITION_
        | RANGE_
        | PRECEDING_
        | UNBOUNDED_
        | CURRENT_
        | FOLLOWING_
        | CUME_DIST_
        | DENSE_RANK_
        | LAG_
        | LAST_VALUE_
        | LEAD_
        | NTH_VALUE_
        | NTILE_
        | PERCENT_RANK_
        | RANK_
        | ROW_NUMBER_
        | GENERATED_
        | ALWAYS_
        | STORED_
        | TRUE_
        | FALSE_
        | WINDOW_
        | NULLS_
        | FIRST_
        | LAST_
        | FILTER_
        | GROUPS_
        | EXCLUDE_
    ;

    name
        : any_name
    ;

    function_name
        : any_name
    ;

    schema_name
        : any_name
    ;

    table_name
        : any_name
    ;

    table_or_index_name
        : any_name
    ;

    column_name
        : any_name
    ;

    collation_name
        : any_name
    ;

    foreign_table
        : any_name
    ;

    index_name
        : any_name
    ;

    trigger_name
        : any_name
    ;

    view_name
        : any_name
    ;

    module_name
        : any_name
    ;

    pragma_name
        : any_name
    ;

    savepoint_name
        : any_name
    ;

    table_alias
        : any_name
    ;

    transaction_name
        : any_name
    ;

    window_name
        : any_name
    ;

    alias
        : any_name
    ;

    filename
        : any_name
    ;

    base_window_name
        : any_name
    ;

    simple_func
        : any_name
    ;

    aggregate_func
        : any_name
    ;

    table_function_name
        : any_name
    ;

    any_name
        : IDENTIFIER
        | keyword
        | STRING_LITERAL
        | OPEN_PAR any_name CLOSE_PAR
    ;

    SCOL      : ';';
    DOT       : '.';
    OPEN_PAR  : '(';
    CLOSE_PAR : ')';
    COMMA     : ',';
    ASSIGN    : '=';
    STAR      : '*';
    PLUS      : '+';
    MINUS     : '-';
    TILDE     : '~';
    PIPE2     : '||';
    DIV       : '/';
    MOD       : '%';
    LT2       : '<<';
    GT2       : '>>';
    AMP       : '&';
    PIPE      : '|';
    LT        : '<';
    LT_EQ     : '<=';
    GT        : '>';
    GT_EQ     : '>=';
    EQ        : '==';
    NOT_EQ1   : '!=';
    NOT_EQ2   : '<>';

    ABORT_             : 'ABORT';
    ACTION_            : 'ACTION';
    ADD_               : 'ADD';
    AFTER_             : 'AFTER';
    ALL_               : 'ALL';
    ALTER_             : 'ALTER';
    ANALYZE_           : 'ANALYZE';
    AND_               : 'AND';
    AS_                : 'AS';
    ASC_               : 'ASC';
    ATTACH_            : 'ATTACH';
    AUTOINCREMENT_     : 'AUTOINCREMENT';
    BEFORE_            : 'BEFORE';
    BEGIN_             : 'BEGIN';
    BETWEEN_           : 'BETWEEN';
    BY_                : 'BY';
    CASCADE_           : 'CASCADE';
    CASE_              : 'CASE';
    CAST_              : 'CAST';
    CHECK_             : 'CHECK';
    COLLATE_           : 'COLLATE';
    COLUMN_            : 'COLUMN';
    COMMIT_            : 'COMMIT';
    CONFLICT_          : 'CONFLICT';
    CONSTRAINT_        : 'CONSTRAINT';
    CREATE_            : 'CREATE';
    CROSS_             : 'CROSS';
    CURRENT_DATE_      : 'CURRENT_DATE';
    CURRENT_TIME_      : 'CURRENT_TIME';
    CURRENT_TIMESTAMP_ : 'CURRENT_TIMESTAMP';
    DATABASE_          : 'DATABASE';
    DEFAULT_           : 'DEFAULT';
    DEFERRABLE_        : 'DEFERRABLE';
    DEFERRED_          : 'DEFERRED';
    DELETE_            : 'DELETE';
    DESC_              : 'DESC';
    DETACH_            : 'DETACH';
    DISTINCT_          : 'DISTINCT';
    DROP_              : 'DROP';
    EACH_              : 'EACH';
    ELSE_              : 'ELSE';
    END_               : 'END';
    ESCAPE_            : 'ESCAPE';
    EXCEPT_            : 'EXCEPT';
    EXCLUSIVE_         : 'EXCLUSIVE';
    EXISTS_            : 'EXISTS';
    EXPLAIN_           : 'EXPLAIN';
    FAIL_              : 'FAIL';
    FOR_               : 'FOR';
    FOREIGN_           : 'FOREIGN';
    FROM_              : 'FROM';
    FULL_              : 'FULL';
    GLOB_              : 'GLOB';
    GROUP_             : 'GROUP';
    HAVING_            : 'HAVING';
    IF_                : 'IF';
    IGNORE_            : 'IGNORE';
    IMMEDIATE_         : 'IMMEDIATE';
    IN_                : 'IN';
    INDEX_             : 'INDEX';
    INDEXED_           : 'INDEXED';
    INITIALLY_         : 'INITIALLY';
    INNER_             : 'INNER';
    INSERT_            : 'INSERT';
    INSTEAD_           : 'INSTEAD';
    INTERSECT_         : 'INTERSECT';
    INTO_              : 'INTO';
    IS_                : 'IS';
    ISNULL_            : 'ISNULL';
    JOIN_              : 'JOIN';
    KEY_               : 'KEY';
    LEFT_              : 'LEFT';
    LIKE_              : 'LIKE';
    LIMIT_             : 'LIMIT';
    MATCH_             : 'MATCH';
    NATURAL_           : 'NATURAL';
    NO_                : 'NO';
    NOT_               : 'NOT';
    NOTNULL_           : 'NOTNULL';
    NULL_              : 'NULL';
    OF_                : 'OF';
    OFFSET_            : 'OFFSET';
    ON_                : 'ON';
    OR_                : 'OR';
    ORDER_             : 'ORDER';
    OUTER_             : 'OUTER';
    PLAN_              : 'PLAN';
    PRAGMA_            : 'PRAGMA';
    PRIMARY_           : 'PRIMARY';
    QUERY_             : 'QUERY';
    RAISE_             : 'RAISE';
    RECURSIVE_         : 'RECURSIVE';
    REFERENCES_        : 'REFERENCES';
    REGEXP_            : 'REGEXP';
    REINDEX_           : 'REINDEX';
    RELEASE_           : 'RELEASE';
    RENAME_            : 'RENAME';
    REPLACE_           : 'REPLACE';
    RESTRICT_          : 'RESTRICT';
    RETURNING_         : 'RETURNING';
    RIGHT_             : 'RIGHT';
    ROLLBACK_          : 'ROLLBACK';
    ROW_               : 'ROW';
    ROWS_              : 'ROWS';
    SAVEPOINT_         : 'SAVEPOINT';
    SELECT_            : 'SELECT';
    SET_               : 'SET';
    TABLE_             : 'TABLE';
    TEMP_              : 'TEMP';
    TEMPORARY_         : 'TEMPORARY';
    THEN_              : 'THEN';
    TO_                : 'TO';
    TRANSACTION_       : 'TRANSACTION';
    TRIGGER_           : 'TRIGGER';
    UNION_             : 'UNION';
    UNIQUE_            : 'UNIQUE';
    UPDATE_            : 'UPDATE';
    USING_             : 'USING';
    VACUUM_            : 'VACUUM';
    VALUES_            : 'VALUES';
    VIEW_              : 'VIEW';
    VIRTUAL_           : 'VIRTUAL';
    WHEN_              : 'WHEN';
    WHERE_             : 'WHERE';
    WITH_              : 'WITH';
    WITHOUT_           : 'WITHOUT';
    FIRST_VALUE_       : 'FIRST_VALUE';
    OVER_              : 'OVER';
    PARTITION_         : 'PARTITION';
    RANGE_             : 'RANGE';
    PRECEDING_         : 'PRECEDING';
    UNBOUNDED_         : 'UNBOUNDED';
    CURRENT_           : 'CURRENT';
    FOLLOWING_         : 'FOLLOWING';
    CUME_DIST_         : 'CUME_DIST';
    DENSE_RANK_        : 'DENSE_RANK';
    LAG_               : 'LAG';
    LAST_VALUE_        : 'LAST_VALUE';
    LEAD_              : 'LEAD';
    NTH_VALUE_         : 'NTH_VALUE';
    NTILE_             : 'NTILE';
    PERCENT_RANK_      : 'PERCENT_RANK';
    RANK_              : 'RANK';
    ROW_NUMBER_        : 'ROW_NUMBER';
    GENERATED_         : 'GENERATED';
    ALWAYS_            : 'ALWAYS';
    STORED_            : 'STORED';
    TRUE_              : 'TRUE';
    FALSE_             : 'FALSE';
    WINDOW_            : 'WINDOW';
    NULLS_             : 'NULLS';
    FIRST_             : 'FIRST';
    LAST_              : 'LAST';
    FILTER_            : 'FILTER';
    GROUPS_            : 'GROUPS';
    EXCLUDE_           : 'EXCLUDE';
    TIES_              : 'TIES';
    OTHERS_            : 'OTHERS';
    DO_                : 'DO';
    NOTHING_           : 'NOTHING';

    IDENTIFIER:
        '"' (~'"' | '""')* '"'
        | '`' (~'`' | '``')* '`'
        | '[' ~']'* ']'
        | [A-Z_\u007F-\uFFFF] [A-Z_0-9\u007F-\uFFFF]*
    ;

    NUMERIC_LITERAL: ((DIGIT+ ('.' DIGIT*)?) | ('.' DIGIT+)) ('E' [-+]? DIGIT+)? | '0x' HEX_DIGIT+;

    BIND_PARAMETER: '?' DIGIT* | [:@$] IDENTIFIER;

    STRING_LITERAL: '\'' ( ~'\'' | '\'\'')* '\'';

    BLOB_LITERAL: 'X' STRING_LITERAL;

    HEX_DIGIT : [0-9A-F];

    DIGIT     : [0-9];
    """

    # Removed:
    # SINGLE_LINE_COMMENT: '--' ~[\r\n]* (('\r'? '\n') | EOF) -> channel(HIDDEN);
    # MULTILINE_COMMENT: '/*' .*? '*/' -> channel(HIDDEN);
    # SPACES: [ \u000B\t\r\n] -> channel(HIDDEN);
    # UNEXPECTED_CHAR: .;
    
    grammar_dict = parse_grammar_string(file_content)
    
    print(json.dumps(grammar_dict, indent=2))

    save_grammar_to_file(grammar_dict, "output_grammar.json")

if __name__ == "__main__":
    main()
    