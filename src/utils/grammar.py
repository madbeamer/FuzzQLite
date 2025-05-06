import sys
import random
import re
import copy
from typing import Dict, Any, List, Tuple, Union, Optional, Set, Callable

START_SYMBOL = "<start>"
RE_NONTERMINAL = re.compile(r'(<[^<> ]*>)')
RE_PARENTHESIZED_EXPR = re.compile(r'\([^()]*\)[?+*]')
RE_EXTENDED_NONTERMINAL = re.compile(r'(<[^<> ]*>[?+*])')

TABLE_CURRENTLY_USED = None

EXISTING_TABLES = {
    "users": {
        "table_name": {"users"},
        "column_name": {"id", "name", "email", "age", "joined_date", "score"},
        "index_name": {"idx_users_email"},
    },
    "products": {
        "table_name": {"products"},
        "column_name": {"id", "name", "price", "category", "stock"},
        "index_name": {"idx_products_category"},
    },
    "orders": {
        "table_name": {"orders"},
        "column_name": {"id", "user_id", "product_id", "quantity", "order_date"},
        "index_name": {"idx_orders_user", "idx_orders_product"},
    },
    "reviews": {
        "table_name": {"reviews"},
        "column_name": {"id", "user_id", "product_id", "rating", "comment"},
        "index_name": set(),
    }
}

def select_random_table() -> None:
    """Select a random table from the existing names."""
    global TABLE_CURRENTLY_USED
    TABLE_CURRENTLY_USED = random.choice(list(EXISTING_TABLES.keys()))
    return None

def use_name(name_category: str) -> Union[None, str]:
    table_stats = EXISTING_TABLES[TABLE_CURRENTLY_USED]
    if len(table_stats[name_category]) == 0:
        return None # If None is returned, it will not interfere with grammar production at all.
    name = random.choice(list(table_stats[name_category]))
    return name
    

# def define_name(name_category: str, table_name: str) -> None:
#     EXISTING_NAMES[name_category].add(table_name)
#     return None

# def use_name(name_category: str) -> Union[None, str]:
#     if len(EXISTING_NAMES[name_category]) == 0:
#         return None # If None is returned, it will not interfere with grammar production at all.
#     name = random.choice(list(EXISTING_NAMES[name_category]))
#     return name

# def clear_all_names() -> None:
#     global EXISTING_NAMES
#     EXISTING_NAMES = {
#         "table_name": set(),
#         "column_name": set(),
#         "savepoint_name": set(),
#         "index_name": set(),
#         "collation_name": set(),
#         "trigger_name": set(),
#         "view_name": set(),
#         "window_name": set(),
#     }
#     return None


Option = Dict[str, Any]


Expansion = Union[str, Tuple[str, Option]]


Grammar = Dict[str, List[Expansion]]


def nonterminals(expansion):
    if isinstance(expansion, tuple):
        expansion = expansion[0]

    return RE_NONTERMINAL.findall(expansion)

def is_nonterminal(s):
    return RE_NONTERMINAL.match(s)

def extend_grammar(grammar: Grammar, extension: Grammar = {}) -> Grammar:
    """Create a copy of `grammar`, updated with `extension`."""
    new_grammar = copy.deepcopy(grammar)
    new_grammar.update(extension)
    return new_grammar

def new_symbol(grammar: Grammar, symbol_name: str = "<symbol>") -> str:
    """Return a new symbol for `grammar` based on `symbol_name`"""
    if symbol_name not in grammar:
        return symbol_name

    count = 1
    while True:
        tentative_symbol_name = symbol_name[:-1] + "-" + repr(count) + ">"
        if tentative_symbol_name not in grammar:
            return tentative_symbol_name
        count += 1

def parenthesized_expressions(expansion: Expansion) -> List[str]:
    if isinstance(expansion, tuple):
        expansion = expansion[0]

    return re.findall(RE_PARENTHESIZED_EXPR, expansion)

def extended_nonterminals(expansion: Expansion) -> List[str]:
    if isinstance(expansion, tuple):
        expansion = expansion[0]

    return re.findall(RE_EXTENDED_NONTERMINAL, expansion)

def convert_ebnf_parentheses(ebnf_grammar: Grammar) -> Grammar:
    """Convert a grammar in extended BNF to BNF"""
    grammar = extend_grammar(ebnf_grammar)
    for nonterminal in ebnf_grammar:
        expansions = ebnf_grammar[nonterminal]

        for i in range(len(expansions)):
            expansion = expansions[i]
            if not isinstance(expansion, str):
                expansion = expansion[0]

            while True:
                parenthesized_exprs = parenthesized_expressions(expansion)
                if len(parenthesized_exprs) == 0:
                    break

                for expr in parenthesized_exprs:
                    operator = expr[-1:]
                    contents = expr[1:-2]

                    new_sym = new_symbol(grammar)

                    exp = grammar[nonterminal][i]
                    opts = None
                    if isinstance(exp, tuple):
                        (exp, opts) = exp
                    assert isinstance(exp, str)

                    expansion = exp.replace(expr, new_sym + operator, 1)
                    if opts:
                        grammar[nonterminal][i] = (expansion, opts)
                    else:
                        grammar[nonterminal][i] = expansion

                    grammar[new_sym] = [contents]

    return grammar

def convert_ebnf_operators(ebnf_grammar: Grammar) -> Grammar:
    """Convert a grammar in extended BNF to BNF"""
    grammar = extend_grammar(ebnf_grammar)
    for nonterminal in ebnf_grammar:
        expansions = ebnf_grammar[nonterminal]

        for i in range(len(expansions)):
            expansion = expansions[i]
            extended_symbols = extended_nonterminals(expansion)

            for extended_symbol in extended_symbols:
                operator = extended_symbol[-1:]
                original_symbol = extended_symbol[:-1]
                assert original_symbol in ebnf_grammar, \
                    f"{original_symbol} is not defined in grammar"

                new_sym = new_symbol(grammar, original_symbol)

                exp = grammar[nonterminal][i]
                opts = None
                if isinstance(exp, tuple):
                    (exp, opts) = exp
                assert isinstance(exp, str)

                new_exp = exp.replace(extended_symbol, new_sym, 1)
                if opts:
                    grammar[nonterminal][i] = (new_exp, opts)
                else:
                    grammar[nonterminal][i] = new_exp

                if operator == '?':
                    grammar[new_sym] = ["", original_symbol]
                elif operator == '*':
                    grammar[new_sym] = ["", original_symbol + new_sym]
                elif operator == '+':
                    grammar[new_sym] = [
                        original_symbol, original_symbol + new_sym]

    return grammar

def convert_ebnf_grammar(ebnf_grammar: Grammar) -> Grammar:
    return convert_ebnf_operators(convert_ebnf_parentheses(ebnf_grammar))

def opts(**kwargs: Any) -> Dict[str, Any]:
    return kwargs

def exp_string(expansion: Expansion) -> str:
    """Return the string to be expanded"""
    if isinstance(expansion, str):
        return expansion
    return expansion[0]

def exp_opts(expansion: Expansion) -> Dict[str, Any]:
    """Return the options of an expansion.  If options are not defined, return {}"""
    if isinstance(expansion, str):
        return {}
    return expansion[1]

def exp_opt(expansion: Expansion, attribute: str) -> Any:
    """Return the given attribution of an expansion.
    If attribute is not defined, return None"""
    return exp_opts(expansion).get(attribute, None)

def set_opts(grammar: Grammar, symbol: str, expansion: Expansion, 
             opts: Option = {}) -> None:
    """Set the options of the given expansion of grammar[symbol] to opts"""
    expansions = grammar[symbol]
    for i, exp in enumerate(expansions):
        if exp_string(exp) != exp_string(expansion):
            continue

        new_opts = exp_opts(exp)
        if opts == {} or new_opts == {}:
            new_opts = opts
        else:
            for key in opts:
                new_opts[key] = opts[key]

        if new_opts == {}:
            grammar[symbol][i] = exp_string(exp)
        else:
            grammar[symbol][i] = (exp_string(exp), new_opts)

        return

    raise KeyError(
        "no expansion " +
        repr(symbol) +
        " -> " +
        repr(
            exp_string(expansion)))

def def_used_nonterminals(grammar: Grammar, start_symbol: 
                          str = START_SYMBOL) -> Tuple[Optional[Set[str]], 
                                                       Optional[Set[str]]]:
    """Return a pair (`defined_nonterminals`, `used_nonterminals`) in `grammar`.
    In case of error, return (`None`, `None`)."""

    defined_nonterminals = set()
    used_nonterminals = {start_symbol}

    for defined_nonterminal in grammar:
        defined_nonterminals.add(defined_nonterminal)
        expansions = grammar[defined_nonterminal]
        if not isinstance(expansions, list):
            print(repr(defined_nonterminal) + ": expansion is not a list",
                  file=sys.stderr)
            return None, None

        if len(expansions) == 0:
            print(repr(defined_nonterminal) + ": expansion list empty",
                  file=sys.stderr)
            return None, None

        for expansion in expansions:
            if isinstance(expansion, tuple):
                expansion = expansion[0]
            if not isinstance(expansion, str):
                print(repr(defined_nonterminal) + ": "
                      + repr(expansion) + ": not a string",
                      file=sys.stderr)
                return None, None

            for used_nonterminal in nonterminals(expansion):
                used_nonterminals.add(used_nonterminal)

    return defined_nonterminals, used_nonterminals

def reachable_nonterminals(grammar: Grammar,
                           start_symbol: str = START_SYMBOL) -> Set[str]:
    reachable = set()

    def _find_reachable_nonterminals(grammar, symbol):
        nonlocal reachable
        reachable.add(symbol)
        for expansion in grammar.get(symbol, []):
            for nonterminal in nonterminals(expansion):
                if nonterminal not in reachable:
                    _find_reachable_nonterminals(grammar, nonterminal)

    _find_reachable_nonterminals(grammar, start_symbol)
    return reachable

def unreachable_nonterminals(grammar: Grammar,
                             start_symbol=START_SYMBOL) -> Set[str]:
    return grammar.keys() - reachable_nonterminals(grammar, start_symbol)

def opts_used(grammar: Grammar) -> Set[str]:
    used_opts = set()
    for symbol in grammar:
        for expansion in grammar[symbol]:
            used_opts |= set(exp_opts(expansion).keys())
    return used_opts

def is_valid_grammar(grammar: Grammar,
                     start_symbol: str = START_SYMBOL, 
                     supported_opts: Set[str] = set()) -> bool:
    """Check if the given `grammar` is valid.
       `start_symbol`: optional start symbol (default: `<start>`)
       `supported_opts`: options supported (default: none)"""

    defined_nonterminals, used_nonterminals = \
        def_used_nonterminals(grammar, start_symbol)
    if defined_nonterminals is None or used_nonterminals is None:
        return False

    # Do not complain about '<start>' being not used,
    # even if start_symbol is different
    if START_SYMBOL in grammar:
        used_nonterminals.add(START_SYMBOL)

    for unused_nonterminal in defined_nonterminals - used_nonterminals:
        print(repr(unused_nonterminal) + ": defined, but not used. Consider applying trim_grammar() on the grammar",
              file=sys.stderr)
    for undefined_nonterminal in used_nonterminals - defined_nonterminals:
        print(repr(undefined_nonterminal) + ": used, but not defined",
              file=sys.stderr)

    # Symbols must be reachable either from <start> or given start symbol
    unreachable = unreachable_nonterminals(grammar, start_symbol)
    msg_start_symbol = start_symbol

    if START_SYMBOL in grammar:
        unreachable = unreachable - \
            reachable_nonterminals(grammar, START_SYMBOL)
        if start_symbol != START_SYMBOL:
            msg_start_symbol += " or " + START_SYMBOL

    for unreachable_nonterminal in unreachable:
        print(repr(unreachable_nonterminal) + ": unreachable from " + msg_start_symbol + ". Consider applying trim_grammar() on the grammar",
              file=sys.stderr)

    used_but_not_supported_opts = set()
    if len(supported_opts) > 0:
        used_but_not_supported_opts = opts_used(
            grammar).difference(supported_opts)
        for opt in used_but_not_supported_opts:
            print(
                "warning: option " +
                repr(opt) +
                " is not supported",
                file=sys.stderr)

    return used_nonterminals == defined_nonterminals and len(unreachable) == 0

def trim_grammar(grammar: Grammar, start_symbol=START_SYMBOL) -> Grammar:
    """Create a copy of `grammar` where all unused and unreachable nonterminals are removed."""
    new_grammar = extend_grammar(grammar)
    defined_nonterminals, used_nonterminals = \
        def_used_nonterminals(grammar, start_symbol)
    if defined_nonterminals is None or used_nonterminals is None:
        return new_grammar

    unused = defined_nonterminals - used_nonterminals
    unreachable = unreachable_nonterminals(grammar, start_symbol)
    for nonterminal in unused | unreachable:
        del new_grammar[nonterminal]

    return new_grammar

def exp_pre_expansion_function(expansion: Expansion) -> Optional[Callable]:
    """Return the specified pre-expansion function, or None if unspecified"""
    return exp_opt(expansion, 'pre')

def exp_post_expansion_function(expansion: Expansion) -> Optional[Callable]:
    """Return the specified post-expansion function, or None if unspecified"""
    return exp_opt(expansion, 'post')

def exp_order(expansion):
    """Return the specified expansion ordering, or None if unspecified"""
    return exp_opt(expansion, 'order')

def set_prob(grammar: Grammar, symbol: str, 
             expansion: Expansion, prob: Optional[float]) -> None:
    """Set the probability of the given expansion of grammar[symbol]"""
    set_opts(grammar, symbol, expansion, opts(prob=prob))

SQL_GRAMMAR: Grammar = {
  "<start>": [
      "<parse>"
  ],
  "<parse>": [
    "<sql_stmt_list>"
  ],
  "<sql_stmt_list>": [
    "<sql_stmt> (<SCOL> <sql_stmt>)* <SCOL>" # Previously: "<SCOL>* <sql_stmt> (<SCOL>+ <sql_stmt>)* <SCOL>*"
  ],
  "<sql_stmt>": [
    "(<EXPLAIN_> (<QUERY_> <PLAN_>)?)? <h1>"
  ],
  "<h1>": [
    "<alter_table_stmt>",
    "<analyze_stmt>",
    "<attach_stmt>",
    "<begin_stmt>",
    "<commit_stmt>",
    "<create_index_stmt>",
    "<create_table_stmt>",
    "<create_trigger_stmt>",
    "<create_view_stmt>",
    "<create_virtual_table_stmt>",
    "<delete_stmt>",
    "<delete_stmt_limited>",
    "<detach_stmt>",
    "<drop_stmt>",
    "<insert_stmt>",
    "<pragma_stmt>",
    "<reindex_stmt>",
    "<release_stmt>",
    "<rollback_stmt>",
    "<savepoint_stmt>",
    "<select_stmt>",
    "<update_stmt>",
    "<update_stmt_limited>",
    "<vacuum_stmt>"
  ],
  "<alter_table_stmt>": [
    "<ALTER_> <TABLE_> (<schema_name> <DOT>)? <table_name> <h3>"
  ],
  "<h2>": [
    "<TO_> <table_name>",
    "<COLUMN_>? <column_name> <TO_> <column_name>"
  ],
  "<h3>": [
    "<RENAME_> <h2>",
    "<ADD_> <COLUMN_>? <column_def>",
    "<DROP_> <COLUMN_>? <column_name>"
  ],
  "<analyze_stmt>": [
    "<ANALYZE_> <h4>?"
  ],
  "<h4>": [
    "<schema_name>",
    "(<schema_name> <DOT>)? <table_or_index_name>"
  ],
  "<attach_stmt>": [
    "<ATTACH_> <DATABASE_>? <expr> <AS_> <schema_name>"
  ],
  "<begin_stmt>": [
    "<BEGIN_> <h5>? (<TRANSACTION_> <transaction_name>?)?"
  ],
  "<h5>": [
    "<DEFERRED_>",
    "<IMMEDIATE_>",
    "<EXCLUSIVE_>"
  ],
  "<commit_stmt>": [
    "<h6> <TRANSACTION_>?"
  ],
  "<h6>": [
    "<COMMIT_>",
    "<END_>"
  ],
  "<rollback_stmt>": [
    "<ROLLBACK_> <TRANSACTION_>? (<TO_> <SAVEPOINT_>? <savepoint_name>)?"
  ],
  "<savepoint_stmt>": [
    "<SAVEPOINT_> <savepoint_name>"
  ],
  "<release_stmt>": [
    "<RELEASE_> <SAVEPOINT_>? <savepoint_name>"
  ],
  "<create_index_stmt>": [
    "<CREATE_> <UNIQUE_>? <INDEX_> (<IF_> <NOT_> <EXISTS_>)? (<schema_name> <DOT>)? <index_name> <ON_> <table_name> <OPEN_PAR> <indexed_column> (<COMMA> <indexed_column>)* <CLOSE_PAR> (<WHERE_> <expr>)?"
  ],
  "<indexed_column>": [
    "<h7> (<COLLATE_> <collation_name>)? <asc_desc>?"
  ],
  "<h7>": [
    "<column_name>",
    "<expr>"
  ],
  "<create_table_stmt>": [
    "<CREATE_> <h8>? <TABLE_> (<IF_> <NOT_> <EXISTS_>)? (<schema_name> <DOT>)? <table_name> <h9>"
  ],
  "<h8>": [
    "<TEMP_>",
    "<TEMPORARY_>"
  ],
  "<h9>": [
    "<OPEN_PAR> <column_def> (<COMMA> <column_def>)* (<COMMA> <table_constraint>)* <CLOSE_PAR> (<WITHOUT_> <IDENTIFIER>)?",
    "<AS_> <select_stmt>"
  ], # Previously: "<OPEN_PAR> <column_def> (<COMMA> <column_def>)*? (<COMMA> <table_constraint>)* <CLOSE_PAR> (<WITHOUT_> row_ROW_ID = <IDENTIFIER>)?", "<AS_> <select_stmt>"
  "<column_def>": [
    "<column_name> <type_name>? <column_constraint>*"
  ],
  "<type_name>": [
    "<name>+ <h10>?"
  ], # Previously: "<name>+? <h10>?"
  "<h10>": [
    "<OPEN_PAR> <signed_number> <CLOSE_PAR>",
    "<OPEN_PAR> <signed_number> <COMMA> <signed_number> <CLOSE_PAR>"
  ],
  "<column_constraint>": [
    "(<CONSTRAINT_> <name>)? <h14>"
  ],
  "<h11>": [
    "<NOT_>? <NULL_>",
    "<UNIQUE_>"
  ],
  "<h12>": [
    "<signed_number>",
    "<literal_value>",
    "<OPEN_PAR> <expr> <CLOSE_PAR>"
  ],
  "<h13>": [
    "<STORED_>",
    "<VIRTUAL_>"
  ],
  "<h14>": [
    "(<PRIMARY_> <KEY_> <asc_desc>? <conflict_clause>? <AUTOINCREMENT_>?)",
    "<h11> <conflict_clause>?",
    "<CHECK_> <OPEN_PAR> <expr> <CLOSE_PAR>",
    "<DEFAULT_> <h12>",
    "<COLLATE_> <collation_name>",
    "<foreign_key_clause>",
    "(<GENERATED_> <ALWAYS_>)? <AS_> <OPEN_PAR> <expr> <CLOSE_PAR> <h13>?"
  ],
  "<signed_number>": [
    "<h15>? <NUMERIC_LITERAL>"
  ],
  "<h15>": [
    "<PLUS>",
    "<MINUS>"
  ],
  "<table_constraint>": [
    "(<CONSTRAINT_> <name>)? <h17>"
  ],
  "<h16>": [
    "<PRIMARY_> <KEY_>",
    "<UNIQUE_>"
  ],
  "<h17>": [
    "<h16> <OPEN_PAR> <indexed_column> (<COMMA> <indexed_column>)* <CLOSE_PAR> <conflict_clause>?",
    "<CHECK_> <OPEN_PAR> <expr> <CLOSE_PAR>",
    "<FOREIGN_> <KEY_> <OPEN_PAR> <column_name> (<COMMA> <column_name>)* <CLOSE_PAR> <foreign_key_clause>"
  ],
  "<foreign_key_clause>": [
    "<REFERENCES_> <foreign_table> (<OPEN_PAR> <column_name> (<COMMA> <column_name>)* <CLOSE_PAR>)? <h21>* <h24>?"
  ],
  "<h18>": [
    "<DELETE_>",
    "<UPDATE_>"
  ],
  "<h19>": [
    "<NULL_>",
    "<DEFAULT_>"
  ],
  "<h20>": [
    "<SET_> <h19>",
    "<CASCADE_>",
    "<RESTRICT_>",
    "<NO_> <ACTION_>"
  ],
  "<h21>": [
    "<ON_> <h18> <h20>",
    "<MATCH_> <name>"
  ],
  "<h22>": [
    "<DEFERRED_>",
    "<IMMEDIATE_>"
  ],
  "<h23>": [
    "<INITIALLY_> <h22>"
  ],
  "<h24>": [
    "<NOT_>? <DEFERRABLE_> <h23>?"
  ],
  "<conflict_clause>": [
    "<ON_> <CONFLICT_> <h25>"
  ],
  "<h25>": [
    "<ROLLBACK_>",
    "<ABORT_>",
    "<FAIL_>",
    "<IGNORE_>",
    "<REPLACE_>"
  ],
  "<create_trigger_stmt>": [
    "<CREATE_> <h26>? <TRIGGER_> (<IF_> <NOT_> <EXISTS_>)? (<schema_name> <DOT>)? <trigger_name> <h27>? <h28> <ON_> <table_name> (<FOR_> <EACH_> <ROW_>)? (<WHEN_> <expr>)? <BEGIN_> <h30>+ <END_>"
  ],
  "<h26>": [
    "<TEMP_>",
    "<TEMPORARY_>"
  ],
  "<h27>": [
    "<BEFORE_>",
    "<AFTER_>",
    "<INSTEAD_> <OF_>"
  ],
  "<h28>": [
    "<DELETE_>",
    "<INSERT_>",
    "<UPDATE_> (<OF_> <column_name> ( <COMMA> <column_name>)*)?"
  ],
  "<h29>": [
    "<update_stmt>",
    "<insert_stmt>",
    "<delete_stmt>",
    "<select_stmt>"
  ],
  "<h30>": [
    "<h29> <SCOL>"
  ],
  "<create_view_stmt>": [
    "<CREATE_> <h31>? <VIEW_> (<IF_> <NOT_> <EXISTS_>)? (<schema_name> <DOT>)? <view_name> (<OPEN_PAR> <column_name> (<COMMA> <column_name>)* <CLOSE_PAR>)? <AS_> <select_stmt>"
  ],
  "<h31>": [
    "<TEMP_>",
    "<TEMPORARY_>"
  ],
  "<create_virtual_table_stmt>": [
    "<CREATE_> <VIRTUAL_> <TABLE_> (<IF_> <NOT_> <EXISTS_>)? (<schema_name> <DOT>)? <table_name> <USING_> <module_name> (<OPEN_PAR> <module_argument> (<COMMA> <module_argument>)* <CLOSE_PAR>)?"
  ],
  "<with_clause>": [
    "<WITH_> <RECURSIVE_>? <cte_table_name> <AS_> <OPEN_PAR> <select_stmt> <CLOSE_PAR> (<COMMA> <cte_table_name> <AS_> <OPEN_PAR> <select_stmt> <CLOSE_PAR>)*"
  ],
  "<cte_table_name>": [
    "<table_name> (<OPEN_PAR> <column_name> ( <COMMA> <column_name>)* <CLOSE_PAR>)?"
  ],
  "<recursive_cte>": [
    "<cte_table_name> <AS_> <OPEN_PAR> <initial_select> <UNION_> <ALL_>? <recursive_select> <CLOSE_PAR>"
  ],
  "<common_table_expression>": [
    "<table_name> (<OPEN_PAR> <column_name> ( <COMMA> <column_name>)* <CLOSE_PAR>)? <AS_> <OPEN_PAR> <select_stmt> <CLOSE_PAR>"
  ],
  "<delete_stmt>": [
    "<with_clause>? <DELETE_> <FROM_> <qualified_table_name> (<WHERE_> <expr>)? <returning_clause>?"
  ],
  "<delete_stmt_limited>": [
    "<with_clause>? <DELETE_> <FROM_> <qualified_table_name> (<WHERE_> <expr>)? <returning_clause>? (<order_by_stmt>? <limit_stmt>)?"
  ],
  "<detach_stmt>": [
    "<DETACH_> <DATABASE_>? <schema_name>"
  ],
  "<drop_stmt>": [
    "<DROP_> <h32> (<IF_> <EXISTS_>)? (<schema_name> <DOT>)? <any_name>"
  ],
  "<h32>": [
    "<INDEX_>",
    "<TABLE_>",
    "<TRIGGER_>",
    "<VIEW_>"
  ],
  "<expr>": [
    "<literal_value>",
    "<BIND_PARAMETER>",
    "((<schema_name> <DOT>)? <table_name> <DOT>)? <column_name>",
    "<unary_operator> <expr>",
    "<expr> <PIPE2> <expr>",
    "<expr> <h33> <expr>",
    "<expr> <h34> <expr>",
    "<expr> <h35> <expr>",
    "<expr> <h36> <expr>",
    "<expr> <h37> <expr>",
    "<expr> <AND_> <expr>",
    "<expr> <OR_> <expr>",
    "<function_name> <OPEN_PAR> <h38>? <CLOSE_PAR> <filter_clause>? <over_clause>?",
    "<OPEN_PAR> <expr> (<COMMA> <expr>)* <CLOSE_PAR>",
    "<CAST_> <OPEN_PAR> <expr> <AS_> <type_name> <CLOSE_PAR>",
    "<expr> <COLLATE_> <collation_name>",
    "<expr> <NOT_>? <h39> <expr> (<ESCAPE_> <expr>)?",
    "<expr> <h40>",
    "<expr> <IS_> <NOT_>? <expr>",
    "<expr> <NOT_>? <BETWEEN_> <expr> <AND_> <expr>",
    "<expr> <NOT_>? <IN_> <h42>",
    "((<NOT_>)? <EXISTS_>)? <OPEN_PAR> <select_stmt> <CLOSE_PAR>",
    "<CASE_> <expr>? (<WHEN_> <expr> <THEN_> <expr>)+ (<ELSE_> <expr>)? <END_>",
    "<raise_function>"
  ],
  "<h33>": [
    "<STAR>",
    "<DIV>",
    "<MOD>"
  ],
  "<h34>": [
    "<PLUS>",
    "<MINUS>"
  ],
  "<h35>": [
    "<LT2>",
    "<GT2>",
    "<AMP>",
    "<PIPE>"
  ],
  "<h36>": [
    "<LT>",
    "<LT_EQ>",
    "<GT>",
    "<GT_EQ>"
  ],
  "<h37>": [
    "<ASSIGN>",
    "<EQ>",
    "<NOT_EQ1>",
    "<NOT_EQ2>",
    "<IS_>",
    "<IS_> <NOT_>",
    "<IS_> <NOT_>? <DISTINCT_> <FROM_>",
    "<IN_>",
    "<LIKE_>",
    "<GLOB_>",
    "<MATCH_>",
    "<REGEXP_>"
  ],
  "<h38>": [
    "(<DISTINCT_>? <expr> ( <COMMA> <expr>)*)",
    "<STAR>"
  ],
  "<h39>": [
    "<LIKE_>",
    "<GLOB_>",
    "<REGEXP_>",
    "<MATCH_>"
  ],
  "<h40>": [
    "<ISNULL_>",
    "<NOTNULL_>",
    "<NOT_> <NULL_>"
  ],
  "<h41>": [
    "<select_stmt>",
    "<expr> (<COMMA> <expr>)*"
  ],
  "<h42>": [
    "<OPEN_PAR> <h41>? <CLOSE_PAR>",
    "(<schema_name> <DOT>)? <table_name>",
    "(<schema_name> <DOT>)? <table_function_name> <OPEN_PAR> (<expr> (<COMMA> <expr>)*)? <CLOSE_PAR>"
  ],
  "<raise_function>": [
    "<RAISE_> <OPEN_PAR> <h44> <CLOSE_PAR>"
  ],
  "<h43>": [
    "<ROLLBACK_>",
    "<ABORT_>",
    "<FAIL_>"
  ],
  "<h44>": [
    "<IGNORE_>",
    "<h43> <COMMA> <error_message>"
  ],
  "<literal_value>": [
    "<NUMERIC_LITERAL>",
    "<STRING_LITERAL>",
    "<BLOB_LITERAL>",
    "<NULL_>",
    "<TRUE_>",
    "<FALSE_>",
    "<CURRENT_TIME_>",
    "<CURRENT_DATE_>",
    "<CURRENT_TIMESTAMP_>"
  ],
  "<value_row>": [
    "<OPEN_PAR> <expr> (<COMMA> <expr>)* <CLOSE_PAR>"
  ],
  "<values_clause>": [
    "<VALUES_> <value_row> (<COMMA> <value_row>)*"
  ],
  "<insert_stmt>": [
    "<with_clause>? <h46> <INTO_> (<schema_name> <DOT>)? <table_name> (<AS_> <table_alias>)? (<OPEN_PAR> <column_name> ( <COMMA> <column_name>)* <CLOSE_PAR>)? <h49> <returning_clause>?"
  ],
  "<h45>": [
    "<REPLACE_>",
    "<ROLLBACK_>",
    "<ABORT_>",
    "<FAIL_>",
    "<IGNORE_>"
  ],
  "<h46>": [
    "<INSERT_>",
    "<REPLACE_>",
    "<INSERT_> <OR_> <h45>"
  ],
  "<h47>": [
    "<values_clause>",
    "<select_stmt>"
  ],
  "<h48>": [
    "<h47> <upsert_clause>?"
  ],
  "<h49>": [
    "<h48>",
    "<DEFAULT_> <VALUES_>"
  ],
  "<returning_clause>": [
    "<RETURNING_> <result_column> (<COMMA> <result_column>)*"
  ],
  "<upsert_clause>": [
    "<ON_> <CONFLICT_> (<OPEN_PAR> <indexed_column> (<COMMA> <indexed_column>)* <CLOSE_PAR> (<WHERE_> <expr>)?)? <DO_> <h54>"
  ],
  "<h50>": [
    "<column_name>",
    "<column_name_list>"
  ],
  "<h51>": [
    "<column_name>",
    "<column_name_list>"
  ],
  "<h52>": [
    "<COMMA> <h51> <ASSIGN> <expr>"
  ],
  "<h53>": [
    "<h50> <ASSIGN> <expr> <h52>* (<WHERE_> <expr>)?"
  ],
  "<h54>": [
    "<NOTHING_>",
    "<UPDATE_> <SET_> <h53>"
  ],
  "<pragma_stmt>": [
    "<PRAGMA_> (<schema_name> <DOT>)? <pragma_name> <h55>?"
  ],
  "<h55>": [
    "<ASSIGN> <pragma_value>",
    "<OPEN_PAR> <pragma_value> <CLOSE_PAR>"
  ],
  "<pragma_value>": [
    "<signed_number>",
    "<name>",
    "<STRING_LITERAL>"
  ],
  "<reindex_stmt>": [
    "<REINDEX_> <h57>?"
  ],
  "<h56>": [
    "<table_name>",
    "<index_name>"
  ],
  "<h57>": [
    "<collation_name>",
    "(<schema_name> <DOT>)? <h56>"
  ],
  "<select_stmt>": [
    "<common_table_stmt>? <select_core> (<compound_operator> <select_core>)* <order_by_stmt>? <limit_stmt>?"
  ],
  "<join_clause>": [
    "<table_or_subquery> (<join_operator> <table_or_subquery> <join_constraint>?)*"
  ],
  "<select_core>": [
    "<h61>",
    "<values_clause>"
  ],
  "<h58>": [
    "<DISTINCT_>",
    "<ALL_>"
  ],
  "<h59>": [
    "<table_or_subquery> (<COMMA> <table_or_subquery>)*",
    "<join_clause>"
  ],
  "<h60>": [
    "<FROM_> <h59>"
  ],
  "<h61>": [
    "<SELECT_> <h58>? <result_column> (<COMMA> <result_column>)* <h60>? (<WHERE_> <expr>)? (<GROUP_> <BY_> <expr> (<COMMA> <expr>)* ( <HAVING_> <expr> )?)? (<WINDOW_> <window_name> <AS_> <window_defn> ( <COMMA> <window_name> <AS_> <window_defn>)*)?"
  ],
  "<factored_select_stmt>": [
    "<select_stmt>"
  ],
  "<simple_select_stmt>": [
    "<common_table_stmt>? <select_core> <order_by_stmt>? <limit_stmt>?"
  ],
  "<compound_select_stmt>": [
    "<common_table_stmt>? <select_core> <h63>+ <order_by_stmt>? <limit_stmt>?"
  ],
  "<h62>": [
    "<UNION_> <ALL_>?",
    "<INTERSECT_>",
    "<EXCEPT_>"
  ],
  "<h63>": [
    "<h62> <select_core>"
  ],
  "<table_or_subquery>": [
    "<h65>",
    "(<schema_name> <DOT>)? <table_function_name> <OPEN_PAR> <expr> (<COMMA> <expr>)* <CLOSE_PAR> (<AS_>? <table_alias>)?",
    "<OPEN_PAR> <h66> <CLOSE_PAR>",
    "<OPEN_PAR> <select_stmt> <CLOSE_PAR> (<AS_>? <table_alias>)?"
  ],
  "<h64>": [
    "<INDEXED_> <BY_> <index_name>",
    "<NOT_> <INDEXED_>"
  ],
  "<h65>": [
    "(<schema_name> <DOT>)? <table_name> (<AS_>? <table_alias>)? <h64>?"
  ],
  "<h66>": [
    "<table_or_subquery> (<COMMA> <table_or_subquery>)*",
    "<join_clause>"
  ],
  "<result_column>": [
    "<STAR>",
    "<table_name> <DOT> <STAR>",
    "<expr> (<AS_>? <column_alias>)?"
  ],
  "<join_operator>": [
    "<COMMA>",
    "<NATURAL_>? <h68>? <JOIN_>"
  ],
  "<h67>": [
    "<LEFT_>",
    "<RIGHT_>",
    "<FULL_>"
  ],
  "<h68>": [
    "<h67> <OUTER_>?",
    "<INNER_>",
    "<CROSS_>"
  ],
  "<join_constraint>": [
    "<ON_> <expr>",
    "<USING_> <OPEN_PAR> <column_name> (<COMMA> <column_name>)* <CLOSE_PAR>"
  ],
  "<compound_operator>": [
    "<UNION_> <ALL_>?",
    "<INTERSECT_>",
    "<EXCEPT_>"
  ],
  "<update_stmt>": [
    "<with_clause>? <UPDATE_> <h70>? <qualified_table_name> <SET_> <h71> <ASSIGN> <expr> <h73>* <h75>? (<WHERE_> <expr>)? <returning_clause>?"
  ],
  "<h69>": [
    "<ROLLBACK_>",
    "<ABORT_>",
    "<REPLACE_>",
    "<FAIL_>",
    "<IGNORE_>"
  ],
  "<h70>": [
    "<OR_> <h69>"
  ],
  "<h71>": [
    "<column_name>",
    "<column_name_list>"
  ],
  "<h72>": [
    "<column_name>",
    "<column_name_list>"
  ],
  "<h73>": [
    "<COMMA> <h72> <ASSIGN> <expr>"
  ],
  "<h74>": [
    "<table_or_subquery> (<COMMA> <table_or_subquery>)*",
    "<join_clause>"
  ],
  "<h75>": [
    "<FROM_> <h74>"
  ],
  "<column_name_list>": [
    "<OPEN_PAR> <column_name> (<COMMA> <column_name>)* <CLOSE_PAR>"
  ],
  "<update_stmt_limited>": [
    "<with_clause>? <UPDATE_> <h77>? <qualified_table_name> <SET_> <h78> <ASSIGN> <expr> <h80>* (<WHERE_> <expr>)? <returning_clause>? (<order_by_stmt>? <limit_stmt>)?"
  ],
  "<h76>": [
    "<ROLLBACK_>",
    "<ABORT_>",
    "<REPLACE_>",
    "<FAIL_>",
    "<IGNORE_>"
  ],
  "<h77>": [
    "<OR_> <h76>"
  ],
  "<h78>": [
    "<column_name>",
    "<column_name_list>"
  ],
  "<h79>": [
    "<column_name>",
    "<column_name_list>"
  ],
  "<h80>": [
    "<COMMA> <h79> <ASSIGN> <expr>"
  ],
  "<qualified_table_name>": [
    "(<schema_name> <DOT>)? <table_name> (<AS_> <alias>)? <h81>?"
  ],
  "<h81>": [
    "<INDEXED_> <BY_> <index_name>",
    "<NOT_> <INDEXED_>"
  ],
  "<vacuum_stmt>": [
    "<VACUUM_> <schema_name>? (<INTO_> <filename>)?"
  ],
  "<filter_clause>": [
    "<FILTER_> <OPEN_PAR> <WHERE_> <expr> <CLOSE_PAR>"
  ],
  "<window_defn>": [
    "<OPEN_PAR> <base_window_name>? (<PARTITION_> <BY_> <expr> (<COMMA> <expr>)*)? (<ORDER_> <BY_> <ordering_term> (<COMMA> <ordering_term>)*) <frame_spec>? <CLOSE_PAR>"
  ],
  "<over_clause>": [
    "<OVER_> <h82>"
  ],
  "<h82>": [
    "<window_name>",
    "<OPEN_PAR> <base_window_name>? (<PARTITION_> <BY_> <expr> (<COMMA> <expr>)*)? (<ORDER_> <BY_> <ordering_term> (<COMMA> <ordering_term>)*)? <frame_spec>? <CLOSE_PAR>"
  ],
  "<frame_spec>": [
    "<frame_clause> <h84>?"
  ],
  "<h83>": [
    "<NO_> <OTHERS_>",
    "<CURRENT_> <ROW_>",
    "<GROUP_>",
    "<TIES_>"
  ],
  "<h84>": [
    "<EXCLUDE_> <h83>"
  ],
  "<frame_clause>": [
    "<h85> <h86>"
  ],
  "<h85>": [
    "<RANGE_>",
    "<ROWS_>",
    "<GROUPS_>"
  ],
  "<h86>": [
    "<frame_single>",
    "<BETWEEN_> <frame_left> <AND_> <frame_right>"
  ],
  "<simple_function_invocation>": [
    "<simple_func> <OPEN_PAR> <h87> <CLOSE_PAR>"
  ],
  "<h87>": [
    "<expr> (<COMMA> <expr>)*",
    "<STAR>"
  ],
  "<aggregate_function_invocation>": [
    "<aggregate_func> <OPEN_PAR> <h88>? <CLOSE_PAR> <filter_clause>?"
  ],
  "<h88>": [
    "<DISTINCT_>? <expr> (<COMMA> <expr>)*",
    "<STAR>"
  ],
  "<window_function_invocation>": [
    "<window_function> <OPEN_PAR> <h89>? <CLOSE_PAR> <filter_clause>? <OVER_> <h90>"
  ],
  "<h89>": [
    "<expr> (<COMMA> <expr>)*",
    "<STAR>"
  ],
  "<h90>": [
    "<window_defn>",
    "<window_name>"
  ],
  "<common_table_stmt>": [
    "<WITH_> <RECURSIVE_>? <common_table_expression> (<COMMA> <common_table_expression>)*"
  ],
  "<order_by_stmt>": [
    "<ORDER_> <BY_> <ordering_term> (<COMMA> <ordering_term>)*"
  ],
  "<limit_stmt>": [
    "<LIMIT_> <expr> <h92>?"
  ],
  "<h91>": [
    "<OFFSET_>",
    "<COMMA>"
  ],
  "<h92>": [
    "<h91> <expr>"
  ],
  "<ordering_term>": [
    "<expr> (<COLLATE_> <collation_name>)? <asc_desc>? <h94>?"
  ],
  "<h93>": [
    "<FIRST_>",
    "<LAST_>"
  ],
  "<h94>": [
    "<NULLS_> <h93>"
  ],
  "<asc_desc>": [
    "<ASC_>",
    "<DESC_>"
  ],
  "<frame_left>": [
    "<expr> <PRECEDING_>",
    "<expr> <FOLLOWING_>",
    "<CURRENT_> <ROW_>",
    "<UNBOUNDED_> <PRECEDING_>"
  ],
  "<frame_right>": [
    "<expr> <PRECEDING_>",
    "<expr> <FOLLOWING_>",
    "<CURRENT_> <ROW_>",
    "<UNBOUNDED_> <FOLLOWING_>"
  ],
  "<frame_single>": [
    "<expr> <PRECEDING_>",
    "<UNBOUNDED_> <PRECEDING_>",
    "<CURRENT_> <ROW_>"
  ],
  "<window_function>": [
    "<h95> <OPEN_PAR> <expr> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by>? <order_by_expr_asc_desc> <frame_clause>? <CLOSE_PAR>",
    "<h96> <OPEN_PAR> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by>? <order_by_expr>? <CLOSE_PAR>",
    "<h97> <OPEN_PAR> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by>? <order_by_expr_asc_desc> <CLOSE_PAR>",
    "<h98> <OPEN_PAR> <expr> <offset>? <default_value>? <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by>? <order_by_expr_asc_desc> <CLOSE_PAR>",
    "<NTH_VALUE_> <OPEN_PAR> <expr> <COMMA> <signed_number> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by>? <order_by_expr_asc_desc> <frame_clause>? <CLOSE_PAR>",
    "<NTILE_> <OPEN_PAR> <expr> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by>? <order_by_expr_asc_desc> <CLOSE_PAR>"
  ],
  "<h95>": [
    "<FIRST_VALUE_>",
    "<LAST_VALUE_>"
  ],
  "<h96>": [
    "<CUME_DIST_>",
    "<PERCENT_RANK_>"
  ],
  "<h97>": [
    "<DENSE_RANK_>",
    "<RANK_>",
    "<ROW_NUMBER_>"
  ],
  "<h98>": [
    "<LAG_>",
    "<LEAD_>"
  ],
  "<offset>": [
    "<COMMA> <signed_number>"
  ],
  "<default_value>": [
    "<COMMA> <signed_number>"
  ],
  "<partition_by>": [
    "<PARTITION_> <BY_> <expr>+"
  ],
  "<order_by_expr>": [
    "<ORDER_> <BY_> <expr>+"
  ],
  "<order_by_expr_asc_desc>": [
    "<ORDER_> <BY_> <expr_asc_desc>"
  ],
  "<expr_asc_desc>": [
    "<expr> <asc_desc>? (<COMMA> <expr> <asc_desc>?)*"
  ],
  "<initial_select>": [
    "<select_stmt>"
  ],
  "<recursive_select>": [
    "<select_stmt>"
  ],
  "<unary_operator>": [
    "<MINUS>",
    "<PLUS>",
    "<TILDE>",
    "<NOT_>"
  ],
  "<error_message>": [
    "<STRING_LITERAL>"
  ],
  "<module_argument>": [
    "<expr>",
    "<column_def>"
  ],
  "<column_alias>": [
    "<IDENTIFIER>",
    "<STRING_LITERAL>"
  ],
  "<keyword>": [
    "<ABORT_>",
    "<ACTION_>",
    "<ADD_>",
    "<AFTER_>",
    "<ALL_>",
    "<ALTER_>",
    "<ANALYZE_>",
    "<AND_>",
    "<AS_>",
    "<ASC_>",
    "<ATTACH_>",
    "<AUTOINCREMENT_>",
    "<BEFORE_>",
    "<BEGIN_>",
    "<BETWEEN_>",
    "<BY_>",
    "<CASCADE_>",
    "<CASE_>",
    "<CAST_>",
    "<CHECK_>",
    "<COLLATE_>",
    "<COLUMN_>",
    "<COMMIT_>",
    "<CONFLICT_>",
    "<CONSTRAINT_>",
    "<CREATE_>",
    "<CROSS_>",
    "<CURRENT_DATE_>",
    "<CURRENT_TIME_>",
    "<CURRENT_TIMESTAMP_>",
    "<DATABASE_>",
    "<DEFAULT_>",
    "<DEFERRABLE_>",
    "<DEFERRED_>",
    "<DELETE_>",
    "<DESC_>",
    "<DETACH_>",
    "<DISTINCT_>",
    "<DROP_>",
    "<EACH_>",
    "<ELSE_>",
    "<END_>",
    "<ESCAPE_>",
    "<EXCEPT_>",
    "<EXCLUSIVE_>",
    "<EXISTS_>",
    "<EXPLAIN_>",
    "<FAIL_>",
    "<FOR_>",
    "<FOREIGN_>",
    "<FROM_>",
    "<FULL_>",
    "<GLOB_>",
    "<GROUP_>",
    "<HAVING_>",
    "<IF_>",
    "<IGNORE_>",
    "<IMMEDIATE_>",
    "<IN_>",
    "<INDEX_>",
    "<INDEXED_>",
    "<INITIALLY_>",
    "<INNER_>",
    "<INSERT_>",
    "<INSTEAD_>",
    "<INTERSECT_>",
    "<INTO_>",
    "<IS_>",
    "<ISNULL_>",
    "<JOIN_>",
    "<KEY_>",
    "<LEFT_>",
    "<LIKE_>",
    "<LIMIT_>",
    "<MATCH_>",
    "<NATURAL_>",
    "<NO_>",
    "<NOT_>",
    "<NOTNULL_>",
    "<NULL_>",
    "<OF_>",
    "<OFFSET_>",
    "<ON_>",
    "<OR_>",
    "<ORDER_>",
    "<OUTER_>",
    "<PLAN_>",
    "<PRAGMA_>",
    "<PRIMARY_>",
    "<QUERY_>",
    "<RAISE_>",
    "<RECURSIVE_>",
    "<REFERENCES_>",
    "<REGEXP_>",
    "<REINDEX_>",
    "<RELEASE_>",
    "<RENAME_>",
    "<REPLACE_>",
    "<RESTRICT_>",
    "<RIGHT_>",
    "<ROLLBACK_>",
    "<ROW_>",
    "<ROWS_>",
    "<SAVEPOINT_>",
    "<SELECT_>",
    "<SET_>",
    "<TABLE_>",
    "<TEMP_>",
    "<TEMPORARY_>",
    "<THEN_>",
    "<TO_>",
    "<TRANSACTION_>",
    "<TRIGGER_>",
    "<UNION_>",
    "<UNIQUE_>",
    "<UPDATE_>",
    "<USING_>",
    "<VACUUM_>",
    "<VALUES_>",
    "<VIEW_>",
    "<VIRTUAL_>",
    "<WHEN_>",
    "<WHERE_>",
    "<WITH_>",
    "<WITHOUT_>",
    "<FIRST_VALUE_>",
    "<OVER_>",
    "<PARTITION_>",
    "<RANGE_>",
    "<PRECEDING_>",
    "<UNBOUNDED_>",
    "<CURRENT_>",
    "<FOLLOWING_>",
    "<CUME_DIST_>",
    "<DENSE_RANK_>",
    "<LAG_>",
    "<LAST_VALUE_>",
    "<LEAD_>",
    "<NTH_VALUE_>",
    "<NTILE_>",
    "<PERCENT_RANK_>",
    "<RANK_>",
    "<ROW_NUMBER_>",
    "<GENERATED_>",
    "<ALWAYS_>",
    "<STORED_>",
    "<TRUE_>",
    "<FALSE_>",
    "<WINDOW_>",
    "<NULLS_>",
    "<FIRST_>",
    "<LAST_>",
    "<FILTER_>",
    "<GROUPS_>",
    "<EXCLUDE_>"
  ],
  "<name>": [
    "<any_name>"
  ],
  "<function_name>": [
    "<any_name>"
  ],
  "<schema_name>": [
    "<any_name>"
  ],
  "<table_name>": [
    "<any_name>"
  ],
  "<table_or_index_name>": [
    "<any_name>"
  ],
  "<column_name>": [
    "<any_name>"
  ],
  "<collation_name>": [
    "<any_name>"
  ],
  "<foreign_table>": [
    "<any_name>"
  ],
  "<index_name>": [
    "<any_name>"
  ],
  "<trigger_name>": [
    "<any_name>"
  ],
  "<view_name>": [
    "<any_name>"
  ],
  "<module_name>": [
    "<any_name>"
  ],
  "<pragma_name>": [
    "<any_name>"
  ],
  "<savepoint_name>": [
    "<any_name>"
  ],
  "<table_alias>": [
    "<any_name>"
  ],
  "<transaction_name>": [
    "<any_name>"
  ],
  "<window_name>": [
    "<any_name>"
  ],
  "<alias>": [
    "<any_name>"
  ],
  "<filename>": [
    "<any_name>"
  ],
  "<base_window_name>": [
    "<any_name>"
  ],
  "<simple_func>": [
    "<any_name>"
  ],
  "<aggregate_func>": [
    "<any_name>"
  ],
  "<table_function_name>": [
    "<any_name>"
  ],
  "<any_name>": [
    "<IDENTIFIER>",
    # "<keyword>", # Previously: Included <keyword> which lead to invalid queries
    "<STRING_LITERAL>",
    # "<OPEN_PAR> <any_name> <CLOSE_PAR>"
  ],
  "<SCOL>": [
    ";"
  ],
  "<DOT>": [
    "."
  ],
  "<OPEN_PAR>": [
    "("
  ],
  "<CLOSE_PAR>": [
    ")"
  ],
  "<COMMA>": [
    ","
  ],
  "<ASSIGN>": [
    "="
  ],
  "<STAR>": [
    "*"
  ],
  "<PLUS>": [
    "+"
  ],
  "<MINUS>": [
    "-"
  ],
  "<TILDE>": [
    "~"
  ],
  "<PIPE2>": [
    "||"
  ],
  "<DIV>": [
    "/"
  ],
  "<MOD>": [
    "%"
  ],
  "<LT2>": [
    "<<"
  ],
  "<GT2>": [
    ">>"
  ],
  "<AMP>": [
    "&"
  ],
  "<PIPE>": [
    "|"
  ],
  "<LT>": [
    "<"
  ],
  "<LT_EQ>": [
    "<="
  ],
  "<GT>": [
    ">"
  ],
  "<GT_EQ>": [
    ">="
  ],
  "<EQ>": [
    "=="
  ],
  "<NOT_EQ1>": [
    "!="
  ],
  "<NOT_EQ2>": [
    "<LT><GT>" # Previously: "<>"
  ],
  "<ABORT_>": [
    "ABORT"
  ],
  "<ACTION_>": [
    "ACTION"
  ],
  "<ADD_>": [
    "ADD"
  ],
  "<AFTER_>": [
    "AFTER"
  ],
  "<ALL_>": [
    "ALL"
  ],
  "<ALTER_>": [
    "ALTER"
  ],
  "<ANALYZE_>": [
    "ANALYZE"
  ],
  "<AND_>": [
    "AND"
  ],
  "<AS_>": [
    "AS"
  ],
  "<ASC_>": [
    "ASC"
  ],
  "<ATTACH_>": [
    "ATTACH"
  ],
  "<AUTOINCREMENT_>": [
    "AUTOINCREMENT"
  ],
  "<BEFORE_>": [
    "BEFORE"
  ],
  "<BEGIN_>": [
    "BEGIN"
  ],
  "<BETWEEN_>": [
    "BETWEEN"
  ],
  "<BY_>": [
    "BY"
  ],
  "<CASCADE_>": [
    "CASCADE"
  ],
  "<CASE_>": [
    "CASE"
  ],
  "<CAST_>": [
    "CAST"
  ],
  "<CHECK_>": [
    "CHECK"
  ],
  "<COLLATE_>": [
    "COLLATE"
  ],
  "<COLUMN_>": [
    "COLUMN"
  ],
  "<COMMIT_>": [
    "COMMIT"
  ],
  "<CONFLICT_>": [
    "CONFLICT"
  ],
  "<CONSTRAINT_>": [
    "CONSTRAINT"
  ],
  "<CREATE_>": [
    "CREATE"
  ],
  "<CROSS_>": [
    "CROSS"
  ],
  "<CURRENT_DATE_>": [
    "CURRENT_DATE"
  ],
  "<CURRENT_TIME_>": [
    "CURRENT_TIME"
  ],
  "<CURRENT_TIMESTAMP_>": [
    "CURRENT_TIMESTAMP"
  ],
  "<DATABASE_>": [
    "DATABASE"
  ],
  "<DEFAULT_>": [
    "DEFAULT"
  ],
  "<DEFERRABLE_>": [
    "DEFERRABLE"
  ],
  "<DEFERRED_>": [
    "DEFERRED"
  ],
  "<DELETE_>": [
    "DELETE"
  ],
  "<DESC_>": [
    "DESC"
  ],
  "<DETACH_>": [
    "DETACH"
  ],
  "<DISTINCT_>": [
    "DISTINCT"
  ],
  "<DROP_>": [
    "DROP"
  ],
  "<EACH_>": [
    "EACH"
  ],
  "<ELSE_>": [
    "ELSE"
  ],
  "<END_>": [
    "END"
  ],
  "<ESCAPE_>": [
    "ESCAPE"
  ],
  "<EXCEPT_>": [
    "EXCEPT"
  ],
  "<EXCLUSIVE_>": [
    "EXCLUSIVE"
  ],
  "<EXISTS_>": [
    "EXISTS"
  ],
  "<EXPLAIN_>": [
    "EXPLAIN"
  ],
  "<FAIL_>": [
    "FAIL"
  ],
  "<FOR_>": [
    "FOR"
  ],
  "<FOREIGN_>": [
    "FOREIGN"
  ],
  "<FROM_>": [
    "FROM"
  ],
  "<FULL_>": [
    "FULL"
  ],
  "<GLOB_>": [
    "GLOB"
  ],
  "<GROUP_>": [
    "GROUP"
  ],
  "<HAVING_>": [
    "HAVING"
  ],
  "<IF_>": [
    "IF"
  ],
  "<IGNORE_>": [
    "IGNORE"
  ],
  "<IMMEDIATE_>": [
    "IMMEDIATE"
  ],
  "<IN_>": [
    "IN"
  ],
  "<INDEX_>": [
    "INDEX"
  ],
  "<INDEXED_>": [
    "INDEXED"
  ],
  "<INITIALLY_>": [
    "INITIALLY"
  ],
  "<INNER_>": [
    "INNER"
  ],
  "<INSERT_>": [
    "INSERT"
  ],
  "<INSTEAD_>": [
    "INSTEAD"
  ],
  "<INTERSECT_>": [
    "INTERSECT"
  ],
  "<INTO_>": [
    "INTO"
  ],
  "<IS_>": [
    "IS"
  ],
  "<ISNULL_>": [
    "ISNULL"
  ],
  "<JOIN_>": [
    "JOIN"
  ],
  "<KEY_>": [
    "KEY"
  ],
  "<LEFT_>": [
    "LEFT"
  ],
  "<LIKE_>": [
    "LIKE"
  ],
  "<LIMIT_>": [
    "LIMIT"
  ],
  "<MATCH_>": [
    "MATCH"
  ],
  "<NATURAL_>": [
    "NATURAL"
  ],
  "<NO_>": [
    "NO"
  ],
  "<NOT_>": [
    "NOT"
  ],
  "<NOTNULL_>": [
    "NOTNULL"
  ],
  "<NULL_>": [
    "NULL"
  ],
  "<OF_>": [
    "OF"
  ],
  "<OFFSET_>": [
    "OFFSET"
  ],
  "<ON_>": [
    "ON"
  ],
  "<OR_>": [
    "OR"
  ],
  "<ORDER_>": [
    "ORDER"
  ],
  "<OUTER_>": [
    "OUTER"
  ],
  "<PLAN_>": [
    "PLAN"
  ],
  "<PRAGMA_>": [
    "PRAGMA"
  ],
  "<PRIMARY_>": [
    "PRIMARY"
  ],
  "<QUERY_>": [
    "QUERY"
  ],
  "<RAISE_>": [
    "RAISE"
  ],
  "<RECURSIVE_>": [
    "RECURSIVE"
  ],
  "<REFERENCES_>": [
    "REFERENCES"
  ],
  "<REGEXP_>": [
    "REGEXP"
  ],
  "<REINDEX_>": [
    "REINDEX"
  ],
  "<RELEASE_>": [
    "RELEASE"
  ],
  "<RENAME_>": [
    "RENAME"
  ],
  "<REPLACE_>": [
    "REPLACE"
  ],
  "<RESTRICT_>": [
    "RESTRICT"
  ],
  "<RETURNING_>": [
    "RETURNING"
  ],
  "<RIGHT_>": [
    "RIGHT"
  ],
  "<ROLLBACK_>": [
    "ROLLBACK"
  ],
  "<ROW_>": [
    "ROW"
  ],
  "<ROWS_>": [
    "ROWS"
  ],
  "<SAVEPOINT_>": [
    "SAVEPOINT"
  ],
  "<SELECT_>": [
    "SELECT"
  ],
  "<SET_>": [
    "SET"
  ],
  "<TABLE_>": [
    "TABLE"
  ],
  "<TEMP_>": [
    "TEMP"
  ],
  "<TEMPORARY_>": [
    "TEMPORARY"
  ],
  "<THEN_>": [
    "THEN"
  ],
  "<TO_>": [
    "TO"
  ],
  "<TRANSACTION_>": [
    "TRANSACTION"
  ],
  "<TRIGGER_>": [
    "TRIGGER"
  ],
  "<UNION_>": [
    "UNION"
  ],
  "<UNIQUE_>": [
    "UNIQUE"
  ],
  "<UPDATE_>": [
    "UPDATE"
  ],
  "<USING_>": [
    "USING"
  ],
  "<VACUUM_>": [
    "VACUUM"
  ],
  "<VALUES_>": [
    "VALUES"
  ],
  "<VIEW_>": [
    "VIEW"
  ],
  "<VIRTUAL_>": [
    "VIRTUAL"
  ],
  "<WHEN_>": [
    "WHEN"
  ],
  "<WHERE_>": [
    "WHERE"
  ],
  "<WITH_>": [
    "WITH"
  ],
  "<WITHOUT_>": [
    "WITHOUT"
  ],
  "<FIRST_VALUE_>": [
    "FIRST_VALUE"
  ],
  "<OVER_>": [
    "OVER"
  ],
  "<PARTITION_>": [
    "PARTITION"
  ],
  "<RANGE_>": [
    "RANGE"
  ],
  "<PRECEDING_>": [
    "PRECEDING"
  ],
  "<UNBOUNDED_>": [
    "UNBOUNDED"
  ],
  "<CURRENT_>": [
    "CURRENT"
  ],
  "<FOLLOWING_>": [
    "FOLLOWING"
  ],
  "<CUME_DIST_>": [
    "CUME_DIST"
  ],
  "<DENSE_RANK_>": [
    "DENSE_RANK"
  ],
  "<LAG_>": [
    "LAG"
  ],
  "<LAST_VALUE_>": [
    "LAST_VALUE"
  ],
  "<LEAD_>": [
    "LEAD"
  ],
  "<NTH_VALUE_>": [
    "NTH_VALUE"
  ],
  "<NTILE_>": [
    "NTILE"
  ],
  "<PERCENT_RANK_>": [
    "PERCENT_RANK"
  ],
  "<RANK_>": [
    "RANK"
  ],
  "<ROW_NUMBER_>": [
    "ROW_NUMBER"
  ],
  "<GENERATED_>": [
    "GENERATED"
  ],
  "<ALWAYS_>": [
    "ALWAYS"
  ],
  "<STORED_>": [
    "STORED"
  ],
  "<TRUE_>": [
    "TRUE"
  ],
  "<FALSE_>": [
    "FALSE"
  ],
  "<WINDOW_>": [
    "WINDOW"
  ],
  "<NULLS_>": [
    "NULLS"
  ],
  "<FIRST_>": [
    "FIRST"
  ],
  "<LAST_>": [
    "LAST"
  ],
  "<FILTER_>": [
    "FILTER"
  ],
  "<GROUPS_>": [
    "GROUPS"
  ],
  "<EXCLUDE_>": [
    "EXCLUDE"
  ],
  "<TIES_>": [
    "TIES"
  ],
  "<OTHERS_>": [
    "OTHERS"
  ],
  "<DO_>": [
    "DO"
  ],
  "<NOTHING_>": [
    "NOTHING"
  ],
  "<IDENTIFIER>": [
      "<LETTER>+<DIGIT>*"
  ],
  "<NUMERIC_LITERAL>": [
      "<DIGIT>+"
  ], # FIXME: Kept very simple
  "<BIND_PARAMETER>": [
      "?<DIGIT>*",
      ":<IDENTIFIER>",
      "@<IDENTIFIER>",
      "$<IDENTIFIER>"
  ],
  "<STRING_LITERAL>": [
      "<LETTER>+"
  ], # FIXME: Kept very simple
  "<BLOB_LITERAL>": [
      "X<STRING_LITERAL>"
  ],
  "<LETTER>": [
      "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
  ],
  "<DIGIT>" : [
      "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
  ],
  "<HEX_DIGIT>": [
      "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"
  ],
}

# BNF_SQL_GRAMMAR = convert_ebnf_grammar(SQL_GRAMMAR) produced:

BNF_SQL_GRAMMAR = {
    "<start>": ["<parse>"],
    "<parse>": ["<sql_stmt_list>"],
    "<sql_stmt_list>": ["<sql_stmt> <symbol-116> <SCOL>"],
    "<sql_stmt>": ["<symbol-2-1> <h1>"],
    "<h1>": [
        "<alter_table_stmt>",
        "<analyze_stmt>",
        "<attach_stmt>",
        "<begin_stmt>",
        "<commit_stmt>",
        "<create_index_stmt>",
        "<create_table_stmt>",
        "<create_trigger_stmt>",
        "<create_view_stmt>",
        "<create_virtual_table_stmt>",
        "<delete_stmt>",
        "<delete_stmt_limited>",
        "<detach_stmt>",
        "<drop_stmt>",
        "<insert_stmt>",
        "<pragma_stmt>",
        "<reindex_stmt>",
        "<release_stmt>",
        "<rollback_stmt>",
        "<savepoint_stmt>",
        "<select_stmt>",
        "<update_stmt>",
        "<update_stmt_limited>",
        "<vacuum_stmt>",
    ],
    "<alter_table_stmt>": ["<ALTER_> <TABLE_> <symbol-3-1> <table_name> <h3>"],
    "<h2>": ["<TO_> <table_name>", "<COLUMN_-1> <column_name> <TO_> <column_name>"],
    "<h3>": [
        "<RENAME_> <h2>",
        "<ADD_> <COLUMN_-2> <column_def>",
        "<DROP_> <COLUMN_-3> <column_name>",
    ],
    "<analyze_stmt>": ["<ANALYZE_> <h4-1>"],
    "<h4>": ["<schema_name>", "<symbol-4-1> <table_or_index_name>"],
    "<attach_stmt>": ["<ATTACH_> <DATABASE_-1> <expr> <AS_> <schema_name>"],
    "<begin_stmt>": ["<BEGIN_> <h5-1> <symbol-5-1>"],
    "<h5>": ["<DEFERRED_>", "<IMMEDIATE_>", "<EXCLUSIVE_>"],
    "<commit_stmt>": ["<h6> <TRANSACTION_-1>"],
    "<h6>": ["<COMMIT_>", "<END_>"],
    "<rollback_stmt>": ["<ROLLBACK_> <TRANSACTION_-2> <symbol-6-1>"],
    "<savepoint_stmt>": ["<SAVEPOINT_> <savepoint_name>"],
    "<release_stmt>": ["<RELEASE_> <SAVEPOINT_-1> <savepoint_name>"],
    "<create_index_stmt>": [
        "<CREATE_> <UNIQUE_-1> <INDEX_> <symbol-7-1> <symbol-8-1> <index_name> <ON_> <table_name> <OPEN_PAR> <indexed_column> <symbol-9-1> <CLOSE_PAR> <symbol-10-1>"
    ],
    "<indexed_column>": ["<h7> <symbol-11-1> <asc_desc-1>"],
    "<h7>": ["<column_name>", "<expr>"],
    "<create_table_stmt>": [
        "<CREATE_> <h8-1> <TABLE_> <symbol-12-1> <symbol-13-1> <table_name> <h9>"
    ],
    "<h8>": ["<TEMP_>", "<TEMPORARY_>"],
    "<h9>": [
        "<OPEN_PAR> <column_def> <symbol-14-1> <symbol-15-1> <CLOSE_PAR> <symbol-16-1>",
        "<AS_> <select_stmt>",
    ],
    "<column_def>": ["<column_name> <type_name-1> <column_constraint-1>"],
    "<type_name>": ["<name-1> <h10-1>"],
    "<h10>": [
        "<OPEN_PAR> <signed_number> <CLOSE_PAR>",
        "<OPEN_PAR> <signed_number> <COMMA> <signed_number> <CLOSE_PAR>",
    ],
    "<column_constraint>": ["<symbol-17-1> <h14>"],
    "<h11>": ["<NOT_-1> <NULL_>", "<UNIQUE_>"],
    "<h12>": ["<signed_number>", "<literal_value>", "<OPEN_PAR> <expr> <CLOSE_PAR>"],
    "<h13>": ["<STORED_>", "<VIRTUAL_>"],
    "<h14>": [
        "(<PRIMARY_> <KEY_> <asc_desc-2> <conflict_clause-1> <AUTOINCREMENT_-1>)",
        "<h11> <conflict_clause-2>",
        "<CHECK_> <OPEN_PAR> <expr> <CLOSE_PAR>",
        "<DEFAULT_> <h12>",
        "<COLLATE_> <collation_name>",
        "<foreign_key_clause>",
        "<symbol-18-1> <AS_> <OPEN_PAR> <expr> <CLOSE_PAR> <h13-1>",
    ],
    "<signed_number>": ["<h15-1> <NUMERIC_LITERAL>"],
    "<h15>": ["<PLUS>", "<MINUS>"],
    "<table_constraint>": ["<symbol-19-1> <h17>"],
    "<h16>": ["<PRIMARY_> <KEY_>", "<UNIQUE_>"],
    "<h17>": [
        "<h16> <OPEN_PAR> <indexed_column> <symbol-20-1> <CLOSE_PAR> <conflict_clause-3>",
        "<CHECK_> <OPEN_PAR> <expr> <CLOSE_PAR>",
        "<FOREIGN_> <KEY_> <OPEN_PAR> <column_name> <symbol-21-1> <CLOSE_PAR> <foreign_key_clause>",
    ],
    "<foreign_key_clause>": [
        "<REFERENCES_> <foreign_table> <symbol-23-1> <h21-1> <h24-1>"
    ],
    "<h18>": ["<DELETE_>", "<UPDATE_>"],
    "<h19>": ["<NULL_>", "<DEFAULT_>"],
    "<h20>": ["<SET_> <h19>", "<CASCADE_>", "<RESTRICT_>", "<NO_> <ACTION_>"],
    "<h21>": ["<ON_> <h18> <h20>", "<MATCH_> <name>"],
    "<h22>": ["<DEFERRED_>", "<IMMEDIATE_>"],
    "<h23>": ["<INITIALLY_> <h22>"],
    "<h24>": ["<NOT_-2> <DEFERRABLE_> <h23-1>"],
    "<conflict_clause>": ["<ON_> <CONFLICT_> <h25>"],
    "<h25>": ["<ROLLBACK_>", "<ABORT_>", "<FAIL_>", "<IGNORE_>", "<REPLACE_>"],
    "<create_trigger_stmt>": [
        "<CREATE_> <h26-1> <TRIGGER_> <symbol-24-1> <symbol-25-1> <trigger_name> <h27-1> <h28> <ON_> <table_name> <symbol-26-1> <symbol-27-1> <BEGIN_> <h30-1> <END_>"
    ],
    "<h26>": ["<TEMP_>", "<TEMPORARY_>"],
    "<h27>": ["<BEFORE_>", "<AFTER_>", "<INSTEAD_> <OF_>"],
    "<h28>": ["<DELETE_>", "<INSERT_>", "<UPDATE_> <symbol-29-1>"],
    "<h29>": ["<update_stmt>", "<insert_stmt>", "<delete_stmt>", "<select_stmt>"],
    "<h30>": ["<h29> <SCOL>"],
    "<create_view_stmt>": [
        "<CREATE_> <h31-1> <VIEW_> <symbol-30-1> <symbol-31-1> <view_name> <symbol-33-1> <AS_> <select_stmt>"
    ],
    "<h31>": ["<TEMP_>", "<TEMPORARY_>"],
    "<create_virtual_table_stmt>": [
        "<CREATE_> <VIRTUAL_> <TABLE_> <symbol-34-1> <symbol-35-1> <table_name> <USING_> <module_name> <symbol-37-1>"
    ],
    "<with_clause>": [
        "<WITH_> <RECURSIVE_-1> <cte_table_name> <AS_> <OPEN_PAR> <select_stmt> <CLOSE_PAR> <symbol-38-1>"
    ],
    "<cte_table_name>": ["<table_name> <symbol-40-1>"],
    "<recursive_cte>": [
        "<cte_table_name> <AS_> <OPEN_PAR> <initial_select> <UNION_> <ALL_-1> <recursive_select> <CLOSE_PAR>"
    ],
    "<common_table_expression>": [
        "<table_name> <symbol-42-1> <AS_> <OPEN_PAR> <select_stmt> <CLOSE_PAR>"
    ],
    "<delete_stmt>": [
        "<with_clause-1> <DELETE_> <FROM_> <qualified_table_name> <symbol-43-1> <returning_clause-1>"
    ],
    "<delete_stmt_limited>": [
        "<with_clause-2> <DELETE_> <FROM_> <qualified_table_name> <symbol-44-1> <returning_clause-2> <symbol-45-1>"
    ],
    "<detach_stmt>": ["<DETACH_> <DATABASE_-2> <schema_name>"],
    "<drop_stmt>": ["<DROP_> <h32> <symbol-46-1> <symbol-47-1> <any_name>"],
    "<h32>": ["<INDEX_>", "<TABLE_>", "<TRIGGER_>", "<VIEW_>"],
    "<expr>": [
        "<literal_value>",
        "<BIND_PARAMETER>",
        "<symbol-49-1> <column_name>",
        "<unary_operator> <expr>",
        "<expr> <PIPE2> <expr>",
        "<expr> <h33> <expr>",
        "<expr> <h34> <expr>",
        "<expr> <h35> <expr>",
        "<expr> <h36> <expr>",
        "<expr> <h37> <expr>",
        "<expr> <AND_> <expr>",
        "<expr> <OR_> <expr>",
        "<function_name> <OPEN_PAR> <h38-1> <CLOSE_PAR> <filter_clause-1> <over_clause-1>",
        "<OPEN_PAR> <expr> <symbol-50-1> <CLOSE_PAR>",
        "<CAST_> <OPEN_PAR> <expr> <AS_> <type_name> <CLOSE_PAR>",
        "<expr> <COLLATE_> <collation_name>",
        "<expr> <NOT_-3> <h39> <expr> <symbol-51-1>",
        "<expr> <h40>",
        "<expr> <IS_> <NOT_-4> <expr>",
        "<expr> <NOT_-5> <BETWEEN_> <expr> <AND_> <expr>",
        "<expr> <NOT_-6> <IN_> <h42>",
        "<symbol-53-1> <OPEN_PAR> <select_stmt> <CLOSE_PAR>",
        "<CASE_> <expr-1> <symbol-54-1> <symbol-55-1> <END_>",
        "<raise_function>",
    ],
    "<h33>": ["<STAR>", "<DIV>", "<MOD>"],
    "<h34>": ["<PLUS>", "<MINUS>"],
    "<h35>": ["<LT2>", "<GT2>", "<AMP>", "<PIPE>"],
    "<h36>": ["<LT>", "<LT_EQ>", "<GT>", "<GT_EQ>"],
    "<h37>": [
        "<ASSIGN>",
        "<EQ>",
        "<NOT_EQ1>",
        "<NOT_EQ2>",
        "<IS_>",
        "<IS_> <NOT_>",
        "<IS_> <NOT_-7> <DISTINCT_> <FROM_>",
        "<IN_>",
        "<LIKE_>",
        "<GLOB_>",
        "<MATCH_>",
        "<REGEXP_>",
    ],
    "<h38>": ["(<DISTINCT_-1> <expr> <symbol-56-1>)", "<STAR>"],
    "<h39>": ["<LIKE_>", "<GLOB_>", "<REGEXP_>", "<MATCH_>"],
    "<h40>": ["<ISNULL_>", "<NOTNULL_>", "<NOT_> <NULL_>"],
    "<h41>": ["<select_stmt>", "<expr> <symbol-57-1>"],
    "<h42>": [
        "<OPEN_PAR> <h41-1> <CLOSE_PAR>",
        "<symbol-58-1> <table_name>",
        "<symbol-59-1> <table_function_name> <OPEN_PAR> <symbol-61-1> <CLOSE_PAR>",
    ],
    "<raise_function>": ["<RAISE_> <OPEN_PAR> <h44> <CLOSE_PAR>"],
    "<h43>": ["<ROLLBACK_>", "<ABORT_>", "<FAIL_>"],
    "<h44>": ["<IGNORE_>", "<h43> <COMMA> <error_message>"],
    "<literal_value>": [
        "<NUMERIC_LITERAL>",
        "<STRING_LITERAL>",
        "<BLOB_LITERAL>",
        "<NULL_>",
        "<TRUE_>",
        "<FALSE_>",
        "<CURRENT_TIME_>",
        "<CURRENT_DATE_>",
        "<CURRENT_TIMESTAMP_>",
    ],
    "<value_row>": ["<OPEN_PAR> <expr> <symbol-62-1> <CLOSE_PAR>"],
    "<values_clause>": ["<VALUES_> <value_row> <symbol-63-1>"],
    "<insert_stmt>": [
        "<with_clause-3> <h46> <INTO_> <symbol-64-1> <table_name> <symbol-65-1> <symbol-67-1> <h49> <returning_clause-3>"
    ],
    "<h45>": ["<REPLACE_>", "<ROLLBACK_>", "<ABORT_>", "<FAIL_>", "<IGNORE_>"],
    "<h46>": ["<INSERT_>", "<REPLACE_>", "<INSERT_> <OR_> <h45>"],
    "<h47>": ["<values_clause>", "<select_stmt>"],
    "<h48>": ["<h47> <upsert_clause-1>"],
    "<h49>": ["<h48>", "<DEFAULT_> <VALUES_>"],
    "<returning_clause>": ["<RETURNING_> <result_column> <symbol-68-1>"],
    "<upsert_clause>": ["<ON_> <CONFLICT_> <symbol-71-1> <DO_> <h54>"],
    "<h50>": ["<column_name>", "<column_name_list>"],
    "<h51>": ["<column_name>", "<column_name_list>"],
    "<h52>": ["<COMMA> <h51> <ASSIGN> <expr>"],
    "<h53>": ["<h50> <ASSIGN> <expr> <h52-1> <symbol-72-1>"],
    "<h54>": ["<NOTHING_>", "<UPDATE_> <SET_> <h53>"],
    "<pragma_stmt>": ["<PRAGMA_> <symbol-73-1> <pragma_name> <h55-1>"],
    "<h55>": ["<ASSIGN> <pragma_value>", "<OPEN_PAR> <pragma_value> <CLOSE_PAR>"],
    "<pragma_value>": ["<signed_number>", "<name>", "<STRING_LITERAL>"],
    "<reindex_stmt>": ["<REINDEX_> <h57-1>"],
    "<h56>": ["<table_name>", "<index_name>"],
    "<h57>": ["<collation_name>", "<symbol-74-1> <h56>"],
    "<select_stmt>": [
        "<common_table_stmt-1> <select_core> <symbol-75-1> <order_by_stmt-1> <limit_stmt-1>"
    ],
    "<join_clause>": ["<table_or_subquery> <symbol-76-1>"],
    "<select_core>": ["<h61>", "<values_clause>"],
    "<h58>": ["<DISTINCT_>", "<ALL_>"],
    "<h59>": ["<table_or_subquery> <symbol-77-1>", "<join_clause>"],
    "<h60>": ["<FROM_> <h59>"],
    "<h61>": [
        "<SELECT_> <h58-1> <result_column> <symbol-78-1> <h60-1> <symbol-79-1> <symbol-83-1> <symbol-84-1>"
    ],
    "<factored_select_stmt>": ["<select_stmt>"],
    "<simple_select_stmt>": [
        "<common_table_stmt-2> <select_core> <order_by_stmt-2> <limit_stmt-2>"
    ],
    "<compound_select_stmt>": [
        "<common_table_stmt-3> <select_core> <h63-1> <order_by_stmt-3> <limit_stmt-3>"
    ],
    "<h62>": ["<UNION_> <ALL_-2>", "<INTERSECT_>", "<EXCEPT_>"],
    "<h63>": ["<h62> <select_core>"],
    "<table_or_subquery>": [
        "<h65>",
        "<symbol-85-1> <table_function_name> <OPEN_PAR> <expr> <symbol-86-1> <CLOSE_PAR> <symbol-87-1>",
        "<OPEN_PAR> <h66> <CLOSE_PAR>",
        "<OPEN_PAR> <select_stmt> <CLOSE_PAR> <symbol-88-1>",
    ],
    "<h64>": ["<INDEXED_> <BY_> <index_name>", "<NOT_> <INDEXED_>"],
    "<h65>": ["<symbol-89-1> <table_name> <symbol-90-1> <h64-1>"],
    "<h66>": ["<table_or_subquery> <symbol-91-1>", "<join_clause>"],
    "<result_column>": ["<STAR>", "<table_name> <DOT> <STAR>", "<expr> <symbol-92-1>"],
    "<join_operator>": ["<COMMA>", "<NATURAL_-1> <h68-1> <JOIN_>"],
    "<h67>": ["<LEFT_>", "<RIGHT_>", "<FULL_>"],
    "<h68>": ["<h67> <OUTER_-1>", "<INNER_>", "<CROSS_>"],
    "<join_constraint>": [
        "<ON_> <expr>",
        "<USING_> <OPEN_PAR> <column_name> <symbol-93-1> <CLOSE_PAR>",
    ],
    "<compound_operator>": ["<UNION_> <ALL_-3>", "<INTERSECT_>", "<EXCEPT_>"],
    "<update_stmt>": [
        "<with_clause-4> <UPDATE_> <h70-1> <qualified_table_name> <SET_> <h71> <ASSIGN> <expr> <h73-1> <h75-1> <symbol-94-1> <returning_clause-4>"
    ],
    "<h69>": ["<ROLLBACK_>", "<ABORT_>", "<REPLACE_>", "<FAIL_>", "<IGNORE_>"],
    "<h70>": ["<OR_> <h69>"],
    "<h71>": ["<column_name>", "<column_name_list>"],
    "<h72>": ["<column_name>", "<column_name_list>"],
    "<h73>": ["<COMMA> <h72> <ASSIGN> <expr>"],
    "<h74>": ["<table_or_subquery> <symbol-95-1>", "<join_clause>"],
    "<h75>": ["<FROM_> <h74>"],
    "<column_name_list>": ["<OPEN_PAR> <column_name> <symbol-96-1> <CLOSE_PAR>"],
    "<update_stmt_limited>": [
        "<with_clause-5> <UPDATE_> <h77-1> <qualified_table_name> <SET_> <h78> <ASSIGN> <expr> <h80-1> <symbol-97-1> <returning_clause-5> <symbol-98-1>"
    ],
    "<h76>": ["<ROLLBACK_>", "<ABORT_>", "<REPLACE_>", "<FAIL_>", "<IGNORE_>"],
    "<h77>": ["<OR_> <h76>"],
    "<h78>": ["<column_name>", "<column_name_list>"],
    "<h79>": ["<column_name>", "<column_name_list>"],
    "<h80>": ["<COMMA> <h79> <ASSIGN> <expr>"],
    "<qualified_table_name>": ["<symbol-99-1> <table_name> <symbol-100-1> <h81-1>"],
    "<h81>": ["<INDEXED_> <BY_> <index_name>", "<NOT_> <INDEXED_>"],
    "<vacuum_stmt>": ["<VACUUM_> <schema_name-1> <symbol-101-1>"],
    "<filter_clause>": ["<FILTER_> <OPEN_PAR> <WHERE_> <expr> <CLOSE_PAR>"],
    "<window_defn>": [
        "<OPEN_PAR> <base_window_name-1> <symbol-104-1> (<ORDER_> <BY_> <ordering_term> <symbol-103-1>) <frame_spec-1> <CLOSE_PAR>"
    ],
    "<over_clause>": ["<OVER_> <h82>"],
    "<h82>": [
        "<window_name>",
        "<OPEN_PAR> <base_window_name-2> <symbol-107-1> <symbol-108-1> <frame_spec-2> <CLOSE_PAR>",
    ],
    "<frame_spec>": ["<frame_clause> <h84-1>"],
    "<h83>": ["<NO_> <OTHERS_>", "<CURRENT_> <ROW_>", "<GROUP_>", "<TIES_>"],
    "<h84>": ["<EXCLUDE_> <h83>"],
    "<frame_clause>": ["<h85> <h86>"],
    "<h85>": ["<RANGE_>", "<ROWS_>", "<GROUPS_>"],
    "<h86>": ["<frame_single>", "<BETWEEN_> <frame_left> <AND_> <frame_right>"],
    "<simple_function_invocation>": ["<simple_func> <OPEN_PAR> <h87> <CLOSE_PAR>"],
    "<h87>": ["<expr> <symbol-109-1>", "<STAR>"],
    "<aggregate_function_invocation>": [
        "<aggregate_func> <OPEN_PAR> <h88-1> <CLOSE_PAR> <filter_clause-2>"
    ],
    "<h88>": ["<DISTINCT_-2> <expr> <symbol-110-1>", "<STAR>"],
    "<window_function_invocation>": [
        "<window_function> <OPEN_PAR> <h89-1> <CLOSE_PAR> <filter_clause-3> <OVER_> <h90>"
    ],
    "<h89>": ["<expr> <symbol-111-1>", "<STAR>"],
    "<h90>": ["<window_defn>", "<window_name>"],
    "<common_table_stmt>": [
        "<WITH_> <RECURSIVE_-2> <common_table_expression> <symbol-112-1>"
    ],
    "<order_by_stmt>": ["<ORDER_> <BY_> <ordering_term> <symbol-113-1>"],
    "<limit_stmt>": ["<LIMIT_> <expr> <h92-1>"],
    "<h91>": ["<OFFSET_>", "<COMMA>"],
    "<h92>": ["<h91> <expr>"],
    "<ordering_term>": ["<expr> <symbol-114-1> <asc_desc-3> <h94-1>"],
    "<h93>": ["<FIRST_>", "<LAST_>"],
    "<h94>": ["<NULLS_> <h93>"],
    "<asc_desc>": ["<ASC_>", "<DESC_>"],
    "<frame_left>": [
        "<expr> <PRECEDING_>",
        "<expr> <FOLLOWING_>",
        "<CURRENT_> <ROW_>",
        "<UNBOUNDED_> <PRECEDING_>",
    ],
    "<frame_right>": [
        "<expr> <PRECEDING_>",
        "<expr> <FOLLOWING_>",
        "<CURRENT_> <ROW_>",
        "<UNBOUNDED_> <FOLLOWING_>",
    ],
    "<frame_single>": [
        "<expr> <PRECEDING_>",
        "<UNBOUNDED_> <PRECEDING_>",
        "<CURRENT_> <ROW_>",
    ],
    "<window_function>": [
        "<h95> <OPEN_PAR> <expr> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by-1> <order_by_expr_asc_desc> <frame_clause-1> <CLOSE_PAR>",
        "<h96> <OPEN_PAR> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by-2> <order_by_expr-1> <CLOSE_PAR>",
        "<h97> <OPEN_PAR> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by-3> <order_by_expr_asc_desc> <CLOSE_PAR>",
        "<h98> <OPEN_PAR> <expr> <offset-1> <default_value-1> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by-4> <order_by_expr_asc_desc> <CLOSE_PAR>",
        "<NTH_VALUE_> <OPEN_PAR> <expr> <COMMA> <signed_number> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by-5> <order_by_expr_asc_desc> <frame_clause-2> <CLOSE_PAR>",
        "<NTILE_> <OPEN_PAR> <expr> <CLOSE_PAR> <OVER_> <OPEN_PAR> <partition_by-6> <order_by_expr_asc_desc> <CLOSE_PAR>",
    ],
    "<h95>": ["<FIRST_VALUE_>", "<LAST_VALUE_>"],
    "<h96>": ["<CUME_DIST_>", "<PERCENT_RANK_>"],
    "<h97>": ["<DENSE_RANK_>", "<RANK_>", "<ROW_NUMBER_>"],
    "<h98>": ["<LAG_>", "<LEAD_>"],
    "<offset>": ["<COMMA> <signed_number>"],
    "<default_value>": ["<COMMA> <signed_number>"],
    "<partition_by>": ["<PARTITION_> <BY_> <expr-2>"],
    "<order_by_expr>": ["<ORDER_> <BY_> <expr-3>"],
    "<order_by_expr_asc_desc>": ["<ORDER_> <BY_> <expr_asc_desc>"],
    "<expr_asc_desc>": ["<expr> <asc_desc-4> <symbol-115-1>"],
    "<initial_select>": ["<select_stmt>"],
    "<recursive_select>": ["<select_stmt>"],
    "<unary_operator>": ["<MINUS>", "<PLUS>", "<TILDE>", "<NOT_>"],
    "<error_message>": ["<STRING_LITERAL>"],
    "<module_argument>": ["<expr>", "<column_def>"],
    "<column_alias>": ["<IDENTIFIER>", "<STRING_LITERAL>"],
    "<keyword>": [
        "<ABORT_>",
        "<ACTION_>",
        "<ADD_>",
        "<AFTER_>",
        "<ALL_>",
        "<ALTER_>",
        "<ANALYZE_>",
        "<AND_>",
        "<AS_>",
        "<ASC_>",
        "<ATTACH_>",
        "<AUTOINCREMENT_>",
        "<BEFORE_>",
        "<BEGIN_>",
        "<BETWEEN_>",
        "<BY_>",
        "<CASCADE_>",
        "<CASE_>",
        "<CAST_>",
        "<CHECK_>",
        "<COLLATE_>",
        "<COLUMN_>",
        "<COMMIT_>",
        "<CONFLICT_>",
        "<CONSTRAINT_>",
        "<CREATE_>",
        "<CROSS_>",
        "<CURRENT_DATE_>",
        "<CURRENT_TIME_>",
        "<CURRENT_TIMESTAMP_>",
        "<DATABASE_>",
        "<DEFAULT_>",
        "<DEFERRABLE_>",
        "<DEFERRED_>",
        "<DELETE_>",
        "<DESC_>",
        "<DETACH_>",
        "<DISTINCT_>",
        "<DROP_>",
        "<EACH_>",
        "<ELSE_>",
        "<END_>",
        "<ESCAPE_>",
        "<EXCEPT_>",
        "<EXCLUSIVE_>",
        "<EXISTS_>",
        "<EXPLAIN_>",
        "<FAIL_>",
        "<FOR_>",
        "<FOREIGN_>",
        "<FROM_>",
        "<FULL_>",
        "<GLOB_>",
        "<GROUP_>",
        "<HAVING_>",
        "<IF_>",
        "<IGNORE_>",
        "<IMMEDIATE_>",
        "<IN_>",
        "<INDEX_>",
        "<INDEXED_>",
        "<INITIALLY_>",
        "<INNER_>",
        "<INSERT_>",
        "<INSTEAD_>",
        "<INTERSECT_>",
        "<INTO_>",
        "<IS_>",
        "<ISNULL_>",
        "<JOIN_>",
        "<KEY_>",
        "<LEFT_>",
        "<LIKE_>",
        "<LIMIT_>",
        "<MATCH_>",
        "<NATURAL_>",
        "<NO_>",
        "<NOT_>",
        "<NOTNULL_>",
        "<NULL_>",
        "<OF_>",
        "<OFFSET_>",
        "<ON_>",
        "<OR_>",
        "<ORDER_>",
        "<OUTER_>",
        "<PLAN_>",
        "<PRAGMA_>",
        "<PRIMARY_>",
        "<QUERY_>",
        "<RAISE_>",
        "<RECURSIVE_>",
        "<REFERENCES_>",
        "<REGEXP_>",
        "<REINDEX_>",
        "<RELEASE_>",
        "<RENAME_>",
        "<REPLACE_>",
        "<RESTRICT_>",
        "<RIGHT_>",
        "<ROLLBACK_>",
        "<ROW_>",
        "<ROWS_>",
        "<SAVEPOINT_>",
        "<SELECT_>",
        "<SET_>",
        "<TABLE_>",
        "<TEMP_>",
        "<TEMPORARY_>",
        "<THEN_>",
        "<TO_>",
        "<TRANSACTION_>",
        "<TRIGGER_>",
        "<UNION_>",
        "<UNIQUE_>",
        "<UPDATE_>",
        "<USING_>",
        "<VACUUM_>",
        "<VALUES_>",
        "<VIEW_>",
        "<VIRTUAL_>",
        "<WHEN_>",
        "<WHERE_>",
        "<WITH_>",
        "<WITHOUT_>",
        "<FIRST_VALUE_>",
        "<OVER_>",
        "<PARTITION_>",
        "<RANGE_>",
        "<PRECEDING_>",
        "<UNBOUNDED_>",
        "<CURRENT_>",
        "<FOLLOWING_>",
        "<CUME_DIST_>",
        "<DENSE_RANK_>",
        "<LAG_>",
        "<LAST_VALUE_>",
        "<LEAD_>",
        "<NTH_VALUE_>",
        "<NTILE_>",
        "<PERCENT_RANK_>",
        "<RANK_>",
        "<ROW_NUMBER_>",
        "<GENERATED_>",
        "<ALWAYS_>",
        "<STORED_>",
        "<TRUE_>",
        "<FALSE_>",
        "<WINDOW_>",
        "<NULLS_>",
        "<FIRST_>",
        "<LAST_>",
        "<FILTER_>",
        "<GROUPS_>",
        "<EXCLUDE_>",
    ],
    "<name>": ["<any_name>"],
    "<function_name>": ["<any_name>"],
    "<schema_name>": ["<any_name>"],
    "<table_name>": ["<any_name>"],
    "<table_or_index_name>": ["<any_name>"],
    "<column_name>": ["<any_name>"],
    "<collation_name>": ["<any_name>"],
    "<foreign_table>": ["<any_name>"],
    "<index_name>": ["<any_name>"],
    "<trigger_name>": ["<any_name>"],
    "<view_name>": ["<any_name>"],
    "<module_name>": ["<any_name>"],
    "<pragma_name>": ["<any_name>"],
    "<savepoint_name>": ["<any_name>"],
    "<table_alias>": ["<any_name>"],
    "<transaction_name>": ["<any_name>"],
    "<window_name>": ["<any_name>"],
    "<alias>": ["<any_name>"],
    "<filename>": ["<any_name>"],
    "<base_window_name>": ["<any_name>"],
    "<simple_func>": ["<any_name>"],
    "<aggregate_func>": ["<any_name>"],
    "<table_function_name>": ["<any_name>"],
    "<any_name>": ["<IDENTIFIER>", "<STRING_LITERAL>"],
    "<SCOL>": [";"],
    "<DOT>": ["."],
    "<OPEN_PAR>": ["("],
    "<CLOSE_PAR>": [")"],
    "<COMMA>": [","],
    "<ASSIGN>": ["="],
    "<STAR>": ["*"],
    "<PLUS>": ["+"],
    "<MINUS>": ["-"],
    "<TILDE>": ["~"],
    "<PIPE2>": ["||"],
    "<DIV>": ["/"],
    "<MOD>": ["%"],
    "<LT2>": ["<<"],
    "<GT2>": [">>"],
    "<AMP>": ["&"],
    "<PIPE>": ["|"],
    "<LT>": ["<"],
    "<LT_EQ>": ["<="],
    "<GT>": [">"],
    "<GT_EQ>": [">="],
    "<EQ>": ["=="],
    "<NOT_EQ1>": ["!="],
    "<NOT_EQ2>": ["<LT><GT>"],
    "<ABORT_>": ["ABORT"],
    "<ACTION_>": ["ACTION"],
    "<ADD_>": ["ADD"],
    "<AFTER_>": ["AFTER"],
    "<ALL_>": ["ALL"],
    "<ALTER_>": ["ALTER"],
    "<ANALYZE_>": ["ANALYZE"],
    "<AND_>": ["AND"],
    "<AS_>": ["AS"],
    "<ASC_>": ["ASC"],
    "<ATTACH_>": ["ATTACH"],
    "<AUTOINCREMENT_>": ["AUTOINCREMENT"],
    "<BEFORE_>": ["BEFORE"],
    "<BEGIN_>": ["BEGIN"],
    "<BETWEEN_>": ["BETWEEN"],
    "<BY_>": ["BY"],
    "<CASCADE_>": ["CASCADE"],
    "<CASE_>": ["CASE"],
    "<CAST_>": ["CAST"],
    "<CHECK_>": ["CHECK"],
    "<COLLATE_>": ["COLLATE"],
    "<COLUMN_>": ["COLUMN"],
    "<COMMIT_>": ["COMMIT"],
    "<CONFLICT_>": ["CONFLICT"],
    "<CONSTRAINT_>": ["CONSTRAINT"],
    "<CREATE_>": ["CREATE"],
    "<CROSS_>": ["CROSS"],
    "<CURRENT_DATE_>": ["CURRENT_DATE"],
    "<CURRENT_TIME_>": ["CURRENT_TIME"],
    "<CURRENT_TIMESTAMP_>": ["CURRENT_TIMESTAMP"],
    "<DATABASE_>": ["DATABASE"],
    "<DEFAULT_>": ["DEFAULT"],
    "<DEFERRABLE_>": ["DEFERRABLE"],
    "<DEFERRED_>": ["DEFERRED"],
    "<DELETE_>": ["DELETE"],
    "<DESC_>": ["DESC"],
    "<DETACH_>": ["DETACH"],
    "<DISTINCT_>": ["DISTINCT"],
    "<DROP_>": ["DROP"],
    "<EACH_>": ["EACH"],
    "<ELSE_>": ["ELSE"],
    "<END_>": ["END"],
    "<ESCAPE_>": ["ESCAPE"],
    "<EXCEPT_>": ["EXCEPT"],
    "<EXCLUSIVE_>": ["EXCLUSIVE"],
    "<EXISTS_>": ["EXISTS"],
    "<EXPLAIN_>": ["EXPLAIN"],
    "<FAIL_>": ["FAIL"],
    "<FOR_>": ["FOR"],
    "<FOREIGN_>": ["FOREIGN"],
    "<FROM_>": ["FROM"],
    "<FULL_>": ["FULL"],
    "<GLOB_>": ["GLOB"],
    "<GROUP_>": ["GROUP"],
    "<HAVING_>": ["HAVING"],
    "<IF_>": ["IF"],
    "<IGNORE_>": ["IGNORE"],
    "<IMMEDIATE_>": ["IMMEDIATE"],
    "<IN_>": ["IN"],
    "<INDEX_>": ["INDEX"],
    "<INDEXED_>": ["INDEXED"],
    "<INITIALLY_>": ["INITIALLY"],
    "<INNER_>": ["INNER"],
    "<INSERT_>": ["INSERT"],
    "<INSTEAD_>": ["INSTEAD"],
    "<INTERSECT_>": ["INTERSECT"],
    "<INTO_>": ["INTO"],
    "<IS_>": ["IS"],
    "<ISNULL_>": ["ISNULL"],
    "<JOIN_>": ["JOIN"],
    "<KEY_>": ["KEY"],
    "<LEFT_>": ["LEFT"],
    "<LIKE_>": ["LIKE"],
    "<LIMIT_>": ["LIMIT"],
    "<MATCH_>": ["MATCH"],
    "<NATURAL_>": ["NATURAL"],
    "<NO_>": ["NO"],
    "<NOT_>": ["NOT"],
    "<NOTNULL_>": ["NOTNULL"],
    "<NULL_>": ["NULL"],
    "<OF_>": ["OF"],
    "<OFFSET_>": ["OFFSET"],
    "<ON_>": ["ON"],
    "<OR_>": ["OR"],
    "<ORDER_>": ["ORDER"],
    "<OUTER_>": ["OUTER"],
    "<PLAN_>": ["PLAN"],
    "<PRAGMA_>": ["PRAGMA"],
    "<PRIMARY_>": ["PRIMARY"],
    "<QUERY_>": ["QUERY"],
    "<RAISE_>": ["RAISE"],
    "<RECURSIVE_>": ["RECURSIVE"],
    "<REFERENCES_>": ["REFERENCES"],
    "<REGEXP_>": ["REGEXP"],
    "<REINDEX_>": ["REINDEX"],
    "<RELEASE_>": ["RELEASE"],
    "<RENAME_>": ["RENAME"],
    "<REPLACE_>": ["REPLACE"],
    "<RESTRICT_>": ["RESTRICT"],
    "<RETURNING_>": ["RETURNING"],
    "<RIGHT_>": ["RIGHT"],
    "<ROLLBACK_>": ["ROLLBACK"],
    "<ROW_>": ["ROW"],
    "<ROWS_>": ["ROWS"],
    "<SAVEPOINT_>": ["SAVEPOINT"],
    "<SELECT_>": ["SELECT"],
    "<SET_>": ["SET"],
    "<TABLE_>": ["TABLE"],
    "<TEMP_>": ["TEMP"],
    "<TEMPORARY_>": ["TEMPORARY"],
    "<THEN_>": ["THEN"],
    "<TO_>": ["TO"],
    "<TRANSACTION_>": ["TRANSACTION"],
    "<TRIGGER_>": ["TRIGGER"],
    "<UNION_>": ["UNION"],
    "<UNIQUE_>": ["UNIQUE"],
    "<UPDATE_>": ["UPDATE"],
    "<USING_>": ["USING"],
    "<VACUUM_>": ["VACUUM"],
    "<VALUES_>": ["VALUES"],
    "<VIEW_>": ["VIEW"],
    "<VIRTUAL_>": ["VIRTUAL"],
    "<WHEN_>": ["WHEN"],
    "<WHERE_>": ["WHERE"],
    "<WITH_>": ["WITH"],
    "<WITHOUT_>": ["WITHOUT"],
    "<FIRST_VALUE_>": ["FIRST_VALUE"],
    "<OVER_>": ["OVER"],
    "<PARTITION_>": ["PARTITION"],
    "<RANGE_>": ["RANGE"],
    "<PRECEDING_>": ["PRECEDING"],
    "<UNBOUNDED_>": ["UNBOUNDED"],
    "<CURRENT_>": ["CURRENT"],
    "<FOLLOWING_>": ["FOLLOWING"],
    "<CUME_DIST_>": ["CUME_DIST"],
    "<DENSE_RANK_>": ["DENSE_RANK"],
    "<LAG_>": ["LAG"],
    "<LAST_VALUE_>": ["LAST_VALUE"],
    "<LEAD_>": ["LEAD"],
    "<NTH_VALUE_>": ["NTH_VALUE"],
    "<NTILE_>": ["NTILE"],
    "<PERCENT_RANK_>": ["PERCENT_RANK"],
    "<RANK_>": ["RANK"],
    "<ROW_NUMBER_>": ["ROW_NUMBER"],
    "<GENERATED_>": ["GENERATED"],
    "<ALWAYS_>": ["ALWAYS"],
    "<STORED_>": ["STORED"],
    "<TRUE_>": ["TRUE"],
    "<FALSE_>": ["FALSE"],
    "<WINDOW_>": ["WINDOW"],
    "<NULLS_>": ["NULLS"],
    "<FIRST_>": ["FIRST"],
    "<LAST_>": ["LAST"],
    "<FILTER_>": ["FILTER"],
    "<GROUPS_>": ["GROUPS"],
    "<EXCLUDE_>": ["EXCLUDE"],
    "<TIES_>": ["TIES"],
    "<OTHERS_>": ["OTHERS"],
    "<DO_>": ["DO"],
    "<NOTHING_>": ["NOTHING"],
    "<IDENTIFIER>": ["<LETTER-1><DIGIT-1>"],
    "<NUMERIC_LITERAL>": ["<DIGIT-2>"],
    "<BIND_PARAMETER>": [
        "?<DIGIT-3>",
        ":<IDENTIFIER>",
        "@<IDENTIFIER>",
        "$<IDENTIFIER>",
    ],
    "<STRING_LITERAL>": ["<LETTER-2>"],
    "<BLOB_LITERAL>": ["X<STRING_LITERAL>"],
    "<LETTER>": [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
    ],
    "<DIGIT>": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    "<HEX_DIGIT>": [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
    ],
    "<symbol>": ["<SCOL-1> <sql_stmt>"],
    "<symbol-1>": ["<QUERY_> <PLAN_>"],
    "<symbol-2>": ["<EXPLAIN_> <symbol-1-1>"],
    "<symbol-3>": ["<schema_name> <DOT>"],
    "<symbol-4>": ["<schema_name> <DOT>"],
    "<symbol-5>": ["<TRANSACTION_> <transaction_name-1>"],
    "<symbol-6>": ["<TO_> <SAVEPOINT_-2> <savepoint_name>"],
    "<symbol-7>": ["<IF_> <NOT_> <EXISTS_>"],
    "<symbol-8>": ["<schema_name> <DOT>"],
    "<symbol-9>": ["<COMMA> <indexed_column>"],
    "<symbol-10>": ["<WHERE_> <expr>"],
    "<symbol-11>": ["<COLLATE_> <collation_name>"],
    "<symbol-12>": ["<IF_> <NOT_> <EXISTS_>"],
    "<symbol-13>": ["<schema_name> <DOT>"],
    "<symbol-14>": ["<COMMA> <column_def>"],
    "<symbol-15>": ["<COMMA> <table_constraint>"],
    "<symbol-16>": ["<WITHOUT_> <IDENTIFIER>"],
    "<symbol-17>": ["<CONSTRAINT_> <name>"],
    "<symbol-18>": ["<GENERATED_> <ALWAYS_>"],
    "<symbol-19>": ["<CONSTRAINT_> <name>"],
    "<symbol-20>": ["<COMMA> <indexed_column>"],
    "<symbol-21>": ["<COMMA> <column_name>"],
    "<symbol-22>": ["<COMMA> <column_name>"],
    "<symbol-23>": ["<OPEN_PAR> <column_name> <symbol-22-1> <CLOSE_PAR>"],
    "<symbol-24>": ["<IF_> <NOT_> <EXISTS_>"],
    "<symbol-25>": ["<schema_name> <DOT>"],
    "<symbol-26>": ["<FOR_> <EACH_> <ROW_>"],
    "<symbol-27>": ["<WHEN_> <expr>"],
    "<symbol-28>": [" <COMMA> <column_name>"],
    "<symbol-29>": ["<OF_> <column_name> <symbol-28-1>"],
    "<symbol-30>": ["<IF_> <NOT_> <EXISTS_>"],
    "<symbol-31>": ["<schema_name> <DOT>"],
    "<symbol-32>": ["<COMMA> <column_name>"],
    "<symbol-33>": ["<OPEN_PAR> <column_name> <symbol-32-1> <CLOSE_PAR>"],
    "<symbol-34>": ["<IF_> <NOT_> <EXISTS_>"],
    "<symbol-35>": ["<schema_name> <DOT>"],
    "<symbol-36>": ["<COMMA> <module_argument>"],
    "<symbol-37>": ["<OPEN_PAR> <module_argument> <symbol-36-1> <CLOSE_PAR>"],
    "<symbol-38>": [
        "<COMMA> <cte_table_name> <AS_> <OPEN_PAR> <select_stmt> <CLOSE_PAR>"
    ],
    "<symbol-39>": [" <COMMA> <column_name>"],
    "<symbol-40>": ["<OPEN_PAR> <column_name> <symbol-39-1> <CLOSE_PAR>"],
    "<symbol-41>": [" <COMMA> <column_name>"],
    "<symbol-42>": ["<OPEN_PAR> <column_name> <symbol-41-1> <CLOSE_PAR>"],
    "<symbol-43>": ["<WHERE_> <expr>"],
    "<symbol-44>": ["<WHERE_> <expr>"],
    "<symbol-45>": ["<order_by_stmt-4> <limit_stmt>"],
    "<symbol-46>": ["<IF_> <EXISTS_>"],
    "<symbol-47>": ["<schema_name> <DOT>"],
    "<symbol-48>": ["<schema_name> <DOT>"],
    "<symbol-49>": ["<symbol-48-1> <table_name> <DOT>"],
    "<symbol-50>": ["<COMMA> <expr>"],
    "<symbol-51>": ["<ESCAPE_> <expr>"],
    "<symbol-52>": ["<NOT_>"],
    "<symbol-53>": ["<symbol-52-1> <EXISTS_>"],
    "<symbol-54>": ["<WHEN_> <expr> <THEN_> <expr>"],
    "<symbol-55>": ["<ELSE_> <expr>"],
    "<symbol-56>": [" <COMMA> <expr>"],
    "<symbol-57>": ["<COMMA> <expr>"],
    "<symbol-58>": ["<schema_name> <DOT>"],
    "<symbol-59>": ["<schema_name> <DOT>"],
    "<symbol-60>": ["<COMMA> <expr>"],
    "<symbol-61>": ["<expr> <symbol-60-1>"],
    "<symbol-62>": ["<COMMA> <expr>"],
    "<symbol-63>": ["<COMMA> <value_row>"],
    "<symbol-64>": ["<schema_name> <DOT>"],
    "<symbol-65>": ["<AS_> <table_alias>"],
    "<symbol-66>": [" <COMMA> <column_name>"],
    "<symbol-67>": ["<OPEN_PAR> <column_name> <symbol-66-1> <CLOSE_PAR>"],
    "<symbol-68>": ["<COMMA> <result_column>"],
    "<symbol-69>": ["<COMMA> <indexed_column>"],
    "<symbol-70>": ["<WHERE_> <expr>"],
    "<symbol-71>": [
        "<OPEN_PAR> <indexed_column> <symbol-69-1> <CLOSE_PAR> <symbol-70-1>"
    ],
    "<symbol-72>": ["<WHERE_> <expr>"],
    "<symbol-73>": ["<schema_name> <DOT>"],
    "<symbol-74>": ["<schema_name> <DOT>"],
    "<symbol-75>": ["<compound_operator> <select_core>"],
    "<symbol-76>": ["<join_operator> <table_or_subquery> <join_constraint-1>"],
    "<symbol-77>": ["<COMMA> <table_or_subquery>"],
    "<symbol-78>": ["<COMMA> <result_column>"],
    "<symbol-79>": ["<WHERE_> <expr>"],
    "<symbol-80>": ["<COMMA> <expr>"],
    "<symbol-81>": [" <HAVING_> <expr> "],
    "<symbol-82>": [" <COMMA> <window_name> <AS_> <window_defn>"],
    "<symbol-83>": ["<GROUP_> <BY_> <expr> <symbol-80-1> <symbol-81-1>"],
    "<symbol-84>": ["<WINDOW_> <window_name> <AS_> <window_defn> <symbol-82-1>"],
    "<symbol-85>": ["<schema_name> <DOT>"],
    "<symbol-86>": ["<COMMA> <expr>"],
    "<symbol-87>": ["<AS_-1> <table_alias>"],
    "<symbol-88>": ["<AS_-2> <table_alias>"],
    "<symbol-89>": ["<schema_name> <DOT>"],
    "<symbol-90>": ["<AS_-3> <table_alias>"],
    "<symbol-91>": ["<COMMA> <table_or_subquery>"],
    "<symbol-92>": ["<AS_-4> <column_alias>"],
    "<symbol-93>": ["<COMMA> <column_name>"],
    "<symbol-94>": ["<WHERE_> <expr>"],
    "<symbol-95>": ["<COMMA> <table_or_subquery>"],
    "<symbol-96>": ["<COMMA> <column_name>"],
    "<symbol-97>": ["<WHERE_> <expr>"],
    "<symbol-98>": ["<order_by_stmt-5> <limit_stmt>"],
    "<symbol-99>": ["<schema_name> <DOT>"],
    "<symbol-100>": ["<AS_> <alias>"],
    "<symbol-101>": ["<INTO_> <filename>"],
    "<symbol-102>": ["<COMMA> <expr>"],
    "<symbol-103>": ["<COMMA> <ordering_term>"],
    "<symbol-104>": ["<PARTITION_> <BY_> <expr> <symbol-102-1>"],
    "<symbol-105>": ["<COMMA> <expr>"],
    "<symbol-106>": ["<COMMA> <ordering_term>"],
    "<symbol-107>": ["<PARTITION_> <BY_> <expr> <symbol-105-1>"],
    "<symbol-108>": ["<ORDER_> <BY_> <ordering_term> <symbol-106-1>"],
    "<symbol-109>": ["<COMMA> <expr>"],
    "<symbol-110>": ["<COMMA> <expr>"],
    "<symbol-111>": ["<COMMA> <expr>"],
    "<symbol-112>": ["<COMMA> <common_table_expression>"],
    "<symbol-113>": ["<COMMA> <ordering_term>"],
    "<symbol-114>": ["<COLLATE_> <collation_name>"],
    "<symbol-115>": ["<COMMA> <expr> <asc_desc-5>"],
    "<symbol-116>": ["", "<symbol><symbol-116>"],
    "<symbol-2-1>": ["", "<symbol-2>"],
    "<symbol-3-1>": ["", "<symbol-3>"],
    "<COLUMN_-1>": ["", "<COLUMN_>"],
    "<COLUMN_-2>": ["", "<COLUMN_>"],
    "<COLUMN_-3>": ["", "<COLUMN_>"],
    "<h4-1>": ["", "<h4>"],
    "<symbol-4-1>": ["", "<symbol-4>"],
    "<DATABASE_-1>": ["", "<DATABASE_>"],
    "<h5-1>": ["", "<h5>"],
    "<symbol-5-1>": ["", "<symbol-5>"],
    "<TRANSACTION_-1>": ["", "<TRANSACTION_>"],
    "<TRANSACTION_-2>": ["", "<TRANSACTION_>"],
    "<symbol-6-1>": ["", "<symbol-6>"],
    "<SAVEPOINT_-1>": ["", "<SAVEPOINT_>"],
    "<UNIQUE_-1>": ["", "<UNIQUE_>"],
    "<symbol-7-1>": ["", "<symbol-7>"],
    "<symbol-8-1>": ["", "<symbol-8>"],
    "<symbol-9-1>": ["", "<symbol-9><symbol-9-1>"],
    "<symbol-10-1>": ["", "<symbol-10>"],
    "<symbol-11-1>": ["", "<symbol-11>"],
    "<asc_desc-1>": ["", "<asc_desc>"],
    "<h8-1>": ["", "<h8>"],
    "<symbol-12-1>": ["", "<symbol-12>"],
    "<symbol-13-1>": ["", "<symbol-13>"],
    "<symbol-14-1>": ["", "<symbol-14><symbol-14-1>"],
    "<symbol-15-1>": ["", "<symbol-15><symbol-15-1>"],
    "<symbol-16-1>": ["", "<symbol-16>"],
    "<type_name-1>": ["", "<type_name>"],
    "<column_constraint-1>": ["", "<column_constraint><column_constraint-1>"],
    "<name-1>": ["<name>", "<name><name-1>"],
    "<h10-1>": ["", "<h10>"],
    "<symbol-17-1>": ["", "<symbol-17>"],
    "<NOT_-1>": ["", "<NOT_>"],
    "<asc_desc-2>": ["", "<asc_desc>"],
    "<conflict_clause-1>": ["", "<conflict_clause>"],
    "<AUTOINCREMENT_-1>": ["", "<AUTOINCREMENT_>"],
    "<conflict_clause-2>": ["", "<conflict_clause>"],
    "<symbol-18-1>": ["", "<symbol-18>"],
    "<h13-1>": ["", "<h13>"],
    "<h15-1>": ["", "<h15>"],
    "<symbol-19-1>": ["", "<symbol-19>"],
    "<symbol-20-1>": ["", "<symbol-20><symbol-20-1>"],
    "<conflict_clause-3>": ["", "<conflict_clause>"],
    "<symbol-21-1>": ["", "<symbol-21><symbol-21-1>"],
    "<symbol-23-1>": ["", "<symbol-23>"],
    "<h21-1>": ["", "<h21><h21-1>"],
    "<h24-1>": ["", "<h24>"],
    "<NOT_-2>": ["", "<NOT_>"],
    "<h23-1>": ["", "<h23>"],
    "<h26-1>": ["", "<h26>"],
    "<symbol-24-1>": ["", "<symbol-24>"],
    "<symbol-25-1>": ["", "<symbol-25>"],
    "<h27-1>": ["", "<h27>"],
    "<symbol-26-1>": ["", "<symbol-26>"],
    "<symbol-27-1>": ["", "<symbol-27>"],
    "<h30-1>": ["<h30>", "<h30><h30-1>"],
    "<symbol-29-1>": ["", "<symbol-29>"],
    "<h31-1>": ["", "<h31>"],
    "<symbol-30-1>": ["", "<symbol-30>"],
    "<symbol-31-1>": ["", "<symbol-31>"],
    "<symbol-33-1>": ["", "<symbol-33>"],
    "<symbol-34-1>": ["", "<symbol-34>"],
    "<symbol-35-1>": ["", "<symbol-35>"],
    "<symbol-37-1>": ["", "<symbol-37>"],
    "<RECURSIVE_-1>": ["", "<RECURSIVE_>"],
    "<symbol-38-1>": ["", "<symbol-38><symbol-38-1>"],
    "<symbol-40-1>": ["", "<symbol-40>"],
    "<ALL_-1>": ["", "<ALL_>"],
    "<symbol-42-1>": ["", "<symbol-42>"],
    "<with_clause-1>": ["", "<with_clause>"],
    "<symbol-43-1>": ["", "<symbol-43>"],
    "<returning_clause-1>": ["", "<returning_clause>"],
    "<with_clause-2>": ["", "<with_clause>"],
    "<symbol-44-1>": ["", "<symbol-44>"],
    "<returning_clause-2>": ["", "<returning_clause>"],
    "<symbol-45-1>": ["", "<symbol-45>"],
    "<DATABASE_-2>": ["", "<DATABASE_>"],
    "<symbol-46-1>": ["", "<symbol-46>"],
    "<symbol-47-1>": ["", "<symbol-47>"],
    "<symbol-49-1>": ["", "<symbol-49>"],
    "<h38-1>": ["", "<h38>"],
    "<filter_clause-1>": ["", "<filter_clause>"],
    "<over_clause-1>": ["", "<over_clause>"],
    "<symbol-50-1>": ["", "<symbol-50><symbol-50-1>"],
    "<NOT_-3>": ["", "<NOT_>"],
    "<symbol-51-1>": ["", "<symbol-51>"],
    "<NOT_-4>": ["", "<NOT_>"],
    "<NOT_-5>": ["", "<NOT_>"],
    "<NOT_-6>": ["", "<NOT_>"],
    "<symbol-53-1>": ["", "<symbol-53>"],
    "<expr-1>": ["", "<expr>"],
    "<symbol-54-1>": ["<symbol-54>", "<symbol-54><symbol-54-1>"],
    "<symbol-55-1>": ["", "<symbol-55>"],
    "<NOT_-7>": ["", "<NOT_>"],
    "<DISTINCT_-1>": ["", "<DISTINCT_>"],
    "<symbol-56-1>": ["", "<symbol-56><symbol-56-1>"],
    "<symbol-57-1>": ["", "<symbol-57><symbol-57-1>"],
    "<h41-1>": ["", "<h41>"],
    "<symbol-58-1>": ["", "<symbol-58>"],
    "<symbol-59-1>": ["", "<symbol-59>"],
    "<symbol-61-1>": ["", "<symbol-61>"],
    "<symbol-62-1>": ["", "<symbol-62><symbol-62-1>"],
    "<symbol-63-1>": ["", "<symbol-63><symbol-63-1>"],
    "<with_clause-3>": ["", "<with_clause>"],
    "<symbol-64-1>": ["", "<symbol-64>"],
    "<symbol-65-1>": ["", "<symbol-65>"],
    "<symbol-67-1>": ["", "<symbol-67>"],
    "<returning_clause-3>": ["", "<returning_clause>"],
    "<upsert_clause-1>": ["", "<upsert_clause>"],
    "<symbol-68-1>": ["", "<symbol-68><symbol-68-1>"],
    "<symbol-71-1>": ["", "<symbol-71>"],
    "<h52-1>": ["", "<h52><h52-1>"],
    "<symbol-72-1>": ["", "<symbol-72>"],
    "<symbol-73-1>": ["", "<symbol-73>"],
    "<h55-1>": ["", "<h55>"],
    "<h57-1>": ["", "<h57>"],
    "<symbol-74-1>": ["", "<symbol-74>"],
    "<common_table_stmt-1>": ["", "<common_table_stmt>"],
    "<symbol-75-1>": ["", "<symbol-75><symbol-75-1>"],
    "<order_by_stmt-1>": ["", "<order_by_stmt>"],
    "<limit_stmt-1>": ["", "<limit_stmt>"],
    "<symbol-76-1>": ["", "<symbol-76><symbol-76-1>"],
    "<symbol-77-1>": ["", "<symbol-77><symbol-77-1>"],
    "<h58-1>": ["", "<h58>"],
    "<symbol-78-1>": ["", "<symbol-78><symbol-78-1>"],
    "<h60-1>": ["", "<h60>"],
    "<symbol-79-1>": ["", "<symbol-79>"],
    "<symbol-83-1>": ["", "<symbol-83>"],
    "<symbol-84-1>": ["", "<symbol-84>"],
    "<common_table_stmt-2>": ["", "<common_table_stmt>"],
    "<order_by_stmt-2>": ["", "<order_by_stmt>"],
    "<limit_stmt-2>": ["", "<limit_stmt>"],
    "<common_table_stmt-3>": ["", "<common_table_stmt>"],
    "<h63-1>": ["<h63>", "<h63><h63-1>"],
    "<order_by_stmt-3>": ["", "<order_by_stmt>"],
    "<limit_stmt-3>": ["", "<limit_stmt>"],
    "<ALL_-2>": ["", "<ALL_>"],
    "<symbol-85-1>": ["", "<symbol-85>"],
    "<symbol-86-1>": ["", "<symbol-86><symbol-86-1>"],
    "<symbol-87-1>": ["", "<symbol-87>"],
    "<symbol-88-1>": ["", "<symbol-88>"],
    "<symbol-89-1>": ["", "<symbol-89>"],
    "<symbol-90-1>": ["", "<symbol-90>"],
    "<h64-1>": ["", "<h64>"],
    "<symbol-91-1>": ["", "<symbol-91><symbol-91-1>"],
    "<symbol-92-1>": ["", "<symbol-92>"],
    "<NATURAL_-1>": ["", "<NATURAL_>"],
    "<h68-1>": ["", "<h68>"],
    "<OUTER_-1>": ["", "<OUTER_>"],
    "<symbol-93-1>": ["", "<symbol-93><symbol-93-1>"],
    "<ALL_-3>": ["", "<ALL_>"],
    "<with_clause-4>": ["", "<with_clause>"],
    "<h70-1>": ["", "<h70>"],
    "<h73-1>": ["", "<h73><h73-1>"],
    "<h75-1>": ["", "<h75>"],
    "<symbol-94-1>": ["", "<symbol-94>"],
    "<returning_clause-4>": ["", "<returning_clause>"],
    "<symbol-95-1>": ["", "<symbol-95><symbol-95-1>"],
    "<symbol-96-1>": ["", "<symbol-96><symbol-96-1>"],
    "<with_clause-5>": ["", "<with_clause>"],
    "<h77-1>": ["", "<h77>"],
    "<h80-1>": ["", "<h80><h80-1>"],
    "<symbol-97-1>": ["", "<symbol-97>"],
    "<returning_clause-5>": ["", "<returning_clause>"],
    "<symbol-98-1>": ["", "<symbol-98>"],
    "<symbol-99-1>": ["", "<symbol-99>"],
    "<symbol-100-1>": ["", "<symbol-100>"],
    "<h81-1>": ["", "<h81>"],
    "<schema_name-1>": ["", "<schema_name>"],
    "<symbol-101-1>": ["", "<symbol-101>"],
    "<base_window_name-1>": ["", "<base_window_name>"],
    "<symbol-104-1>": ["", "<symbol-104>"],
    "<symbol-103-1>": ["", "<symbol-103><symbol-103-1>"],
    "<frame_spec-1>": ["", "<frame_spec>"],
    "<base_window_name-2>": ["", "<base_window_name>"],
    "<symbol-107-1>": ["", "<symbol-107>"],
    "<symbol-108-1>": ["", "<symbol-108>"],
    "<frame_spec-2>": ["", "<frame_spec>"],
    "<h84-1>": ["", "<h84>"],
    "<symbol-109-1>": ["", "<symbol-109><symbol-109-1>"],
    "<h88-1>": ["", "<h88>"],
    "<filter_clause-2>": ["", "<filter_clause>"],
    "<DISTINCT_-2>": ["", "<DISTINCT_>"],
    "<symbol-110-1>": ["", "<symbol-110><symbol-110-1>"],
    "<h89-1>": ["", "<h89>"],
    "<filter_clause-3>": ["", "<filter_clause>"],
    "<symbol-111-1>": ["", "<symbol-111><symbol-111-1>"],
    "<RECURSIVE_-2>": ["", "<RECURSIVE_>"],
    "<symbol-112-1>": ["", "<symbol-112><symbol-112-1>"],
    "<symbol-113-1>": ["", "<symbol-113><symbol-113-1>"],
    "<h92-1>": ["", "<h92>"],
    "<symbol-114-1>": ["", "<symbol-114>"],
    "<asc_desc-3>": ["", "<asc_desc>"],
    "<h94-1>": ["", "<h94>"],
    "<partition_by-1>": ["", "<partition_by>"],
    "<frame_clause-1>": ["", "<frame_clause>"],
    "<partition_by-2>": ["", "<partition_by>"],
    "<order_by_expr-1>": ["", "<order_by_expr>"],
    "<partition_by-3>": ["", "<partition_by>"],
    "<offset-1>": ["", "<offset>"],
    "<default_value-1>": ["", "<default_value>"],
    "<partition_by-4>": ["", "<partition_by>"],
    "<partition_by-5>": ["", "<partition_by>"],
    "<frame_clause-2>": ["", "<frame_clause>"],
    "<partition_by-6>": ["", "<partition_by>"],
    "<expr-2>": ["<expr>", "<expr><expr-2>"],
    "<expr-3>": ["<expr>", "<expr><expr-3>"],
    "<asc_desc-4>": ["", "<asc_desc>"],
    "<symbol-115-1>": ["", "<symbol-115><symbol-115-1>"],
    "<LETTER-1>": ["<LETTER>", "<LETTER><LETTER-1>"],
    "<DIGIT-1>": ["", "<DIGIT><DIGIT-1>"],
    "<DIGIT-2>": ["<DIGIT>", "<DIGIT><DIGIT-2>"],
    "<DIGIT-3>": ["", "<DIGIT><DIGIT-3>"],
    "<LETTER-2>": ["<LETTER>", "<LETTER><LETTER-2>"],
    "<SCOL-1>": ["<SCOL>"], # Was <SCOL><SCOL-1> on second element, left one was <SCOL>
    "<symbol-1-1>": ["", "<symbol-1>"],
    "<transaction_name-1>": ["", "<transaction_name>"],
    "<SAVEPOINT_-2>": ["", "<SAVEPOINT_>"],
    "<symbol-22-1>": ["", "<symbol-22><symbol-22-1>"],
    "<symbol-28-1>": ["", "<symbol-28><symbol-28-1>"],
    "<symbol-32-1>": ["", "<symbol-32><symbol-32-1>"],
    "<symbol-36-1>": ["", "<symbol-36><symbol-36-1>"],
    "<symbol-39-1>": ["", "<symbol-39><symbol-39-1>"],
    "<symbol-41-1>": ["", "<symbol-41><symbol-41-1>"],
    "<order_by_stmt-4>": ["", "<order_by_stmt>"],
    "<symbol-48-1>": ["", "<symbol-48>"],
    "<symbol-52-1>": ["", "<symbol-52>"],
    "<symbol-60-1>": ["", "<symbol-60><symbol-60-1>"],
    "<symbol-66-1>": ["", "<symbol-66><symbol-66-1>"],
    "<symbol-69-1>": ["", "<symbol-69><symbol-69-1>"],
    "<symbol-70-1>": ["", "<symbol-70>"],
    "<join_constraint-1>": ["", "<join_constraint>"],
    "<symbol-80-1>": ["", "<symbol-80><symbol-80-1>"],
    "<symbol-81-1>": ["", "<symbol-81>"],
    "<symbol-82-1>": ["", "<symbol-82><symbol-82-1>"],
    "<AS_-1>": ["", "<AS_>"],
    "<AS_-2>": ["", "<AS_>"],
    "<AS_-3>": ["", "<AS_>"],
    "<AS_-4>": ["", "<AS_>"],
    "<order_by_stmt-5>": ["", "<order_by_stmt>"],
    "<symbol-102-1>": ["", "<symbol-102><symbol-102-1>"],
    "<symbol-105-1>": ["", "<symbol-105><symbol-105-1>"],
    "<symbol-106-1>": ["", "<symbol-106><symbol-106-1>"],
    "<asc_desc-5>": ["", "<asc_desc>"],
}

# SAVE_NAMES_CREATE_TABLE_BNF_SQL_GRAMMAR = extend_grammar(BNF_SQL_GRAMMAR,
#   {
#       # Remove EXPLAIN part from grammar
#       "<sql_stmt>": ["<h1>"], # Was: "<symbol-2-1> <h1>"

#       # Hardcode schema name to "main"
#       "<schema_name>": ["main"],

#       # Force SELECT * to use SELECT * FROM <something>
#       "<h60-1>": ["<h60>", "<h60>"],

#       # Remove TEMP or TEMPORARY from <create_table_stmt>
#       "<create_table_stmt>": [
#           "<CREATE_> <TABLE_> <symbol-12-1> <symbol-13-1> <table_name> <h9>" # Was: <CREATE_> <h8-1> <TABLE_> <symbol-12-1> <symbol-13-1> <table_name> <h9>
#       ],

#        # Reduce the number of letters
#       "<LETTER>": [
#           "a",
#           "b",
#           "c",
#           "d",
#           "e",
#           "f",
#           "g",
#       ],

#       # Set <STRING_LITERAL> to single letter
#       "<STRING_LITERAL>": ["<LETTER>"],

#       # Enforce LIMIT to be followed by DIGIT
#       "<limit_stmt>": ["<LIMIT_> <DIGIT>"],

#       # Remove ORDER BY statement
#       "<order_by_stmt-1>": [""],
#       "<order_by_stmt-2>": [""],
#       "<order_by_stmt-3>": [""],
#       "<order_by_stmt-4>": [""],
#       "<order_by_stmt-5>": [""],

#       "<sql_stmt_list>": [("<create_table_stmt> <SCOL>", opts(pre=clear_all_names))], # Could add: ("<create_virtual_table_stmt> <SCOL>", opts(pre=clear_all_names))
#       "<table_name>": [
#           ("<any_name>",
#            opts(post=lambda table_name: define_name('table_name', table_name))
#           )
#       ],
#       "<column_name>": [
#           ("<any_name>",
#            opts(post=lambda column_name: define_name('column_name', column_name))
#           )
#       ],
#       "<savepoint_name>": [
#           ("<any_name>",
#            opts(post=lambda savepoint_name: define_name('savepoint_name', savepoint_name))
#           )
#       ],
#       "<index_name>": [
#           ("<any_name>",
#            opts(post=lambda index_name: define_name('index_name', index_name))
#           )
#       ],
#       "<collation_name>": [
#           ("<any_name>",
#            opts(post=lambda collation_name: define_name('collation_name', collation_name))
#           )
#       ],
#       "<trigger_name>": [
#           ("<any_name>",
#            opts(post=lambda trigger_name: define_name('trigger_name', trigger_name))
#           )
#       ],
#       "<view_name>": [
#           ("<any_name>",
#            opts(post=lambda view_name: define_name('view_name', view_name))
#           )
#       ],
#       "<window_name>": [
#           ("<any_name>",
#            opts(post=lambda window_name: define_name('window_name', window_name))
#           )
#       ]
#   }
# )

USE_NAMES_BNF_SQL_GRAMMAR = extend_grammar(BNF_SQL_GRAMMAR,
  {
      # Only do one statement
      "<sql_stmt_list>": ["<sql_stmt> <SCOL>"], # Was "<sql_stmt> <symbol-116> <SCOL>"

      # Remove EXPLAIN part from grammar
      "<sql_stmt>": ["<h1>"], # Was: "<symbol-2-1> <h1>"

      # Force SELECT * to use SELECT * FROM <something>
      "<h60-1>": ["<h60>", "<h60>"],

      # Reduce the number of letters
      "<LETTER>": [
          "a",
          "b",
          "c",
          "d",
          "e",
          "f",
          "g",
      ],

      # Set <STRING_LITERAL> to single letter
      "<STRING_LITERAL>": ["<LETTER>"],

      # Remove some statements that are not relevant for the test
      "<h1>": [
        "<alter_table_stmt>",
        # "<analyze_stmt>",
        "<attach_stmt>",
        "<begin_stmt>",
        "<commit_stmt>",
        "<create_index_stmt>",
        "<create_table_stmt>", # We might remove this
        "<create_trigger_stmt>",
        "<create_view_stmt>",
        "<create_virtual_table_stmt>", # We might remove this
        "<delete_stmt>",
        "<delete_stmt_limited>",
        "<detach_stmt>",
        "<drop_stmt>",
        "<insert_stmt>",
        # "<pragma_stmt>",
        "<reindex_stmt>",
        "<release_stmt>",
        "<rollback_stmt>",
        "<savepoint_stmt>",
        "<select_stmt>",
        "<update_stmt>",
        "<update_stmt_limited>",
        "<vacuum_stmt>",
      ],

      # # Remove <BIND_PARAMETER> from grammar
      # "<expr>": [
      #   "<literal_value>",
      #   # "<BIND_PARAMETER>",
      #   "<symbol-49-1> <column_name>",
      #   "<unary_operator> <expr>",
      #   "<expr> <PIPE2> <expr>",
      #   "<expr> <h33> <expr>",
      #   "<expr> <h34> <expr>",
      #   "<expr> <h35> <expr>",
      #   "<expr> <h36> <expr>",
      #   "<expr> <h37> <expr>",
      #   "<expr> <AND_> <expr>",
      #   "<expr> <OR_> <expr>",
      #   "<function_name> <OPEN_PAR> <h38-1> <CLOSE_PAR> <filter_clause-1> <over_clause-1>",
      #   "<OPEN_PAR> <expr> <symbol-50-1> <CLOSE_PAR>",
      #   "<CAST_> <OPEN_PAR> <expr> <AS_> <type_name> <CLOSE_PAR>",
      #   "<expr> <COLLATE_> <collation_name>",
      #   "<expr> <NOT_-3> <h39> <expr> <symbol-51-1>",
      #   "<expr> <h40>",
      #   "<expr> <IS_> <NOT_-4> <expr>",
      #   "<expr> <NOT_-5> <BETWEEN_> <expr> <AND_> <expr>",
      #   "<expr> <NOT_-6> <IN_> <h42>",
      #   "<symbol-53-1> <OPEN_PAR> <select_stmt> <CLOSE_PAR>",
      #   "<CASE_> <expr-1> <symbol-54-1> <symbol-55-1> <END_>",
      #   "<raise_function>",
      # ],

      # Hardcode schema name to "main" (for example small.db becomes automatically main)
      "<schema_name>": ["main"],

      # Add all supported sqlite types
      "<type_name>": [
          "INTEGER",
          "INT",
          "TINYINT",
          "SMALLINT",
          "MEDIUMINT",
          "BIGINT",
          "UNSIGNED BIG INT",
          "INT2",
          "INT8",
          "TEXT",
          "CHARACTER",
          "VARCHAR",
          "VARYING CHARACTER",
          "NCHAR",
          "NATIVE CHARACTER",
          "NVARCHAR",
          "CLOB",
          "REAL",
          "DOUBLE",
          "DOUBLE PRECISION",
          "FLOAT",
          "NUMERIC",
          "DECIMAL",
          "BOOLEAN",
          "DATE",
          "DATETIME",
          "BLOB",
          "NONE"
      ],

      # Add all supported pragma names and values
      "<pragma_name>": [
        "analysis_limit",
        "auto_vacuum",
        "automatic_index",
        "busy_timeout",
        "cache_size",
        "cache_spill",
        "cell_size_check",
        "checkpoint_fullfsync",
        "collation_list",
        "compile_options",
        "data_store_directory",
        "data_version",
        "database_list",
        "defer_foreign_keys",
        "empty_result_callbacks",
        "encoding",
        "foreign_key_check",
        "foreign_key_list",
        "foreign_keys",
        "freelist_count",
        "fullfsync",
        "function_list",
        "hard_heap_limit",
        "ignore_check_constraints",
        "incremental_vacuum",
        "index_info",
        "index_list",
        "index_xinfo",
        "integrity_check",
        "journal_mode",
        "journal_size_limit",
        "legacy_alter_table",
        "legacy_file_format",
        "locking_mode",
        "max_page_count",
        "mmap_size",
        "module_list",
        "optimize",
        "page_count",
        "page_size",
        "parser_trace",
        "pragma_list",
        "query_only",
        "quick_check",
        "read_uncommitted",
        "recursive_triggers",
        "reverse_unordered_selects",
        "schema_version",
        "secure_delete",
        "shrink_memory",
        "soft_heap_limit",
        "stats",
        "synchronous",
        "table_info",
        "table_list",
        "table_xinfo",
        "temp_store",
        "temp_store_directory",
        "threads",
        "trusted_schema",
        "user_version",
        "vdbe_addoptrace",
        "vdbe_debug",
        "vdbe_listing",
        "vdbe_trace",
        "wal_autocheckpoint",
        "wal_checkpoint",
        "writable_schema"
      ],

      "<pragma_value>": [
        # "<signed_number>", # I think this is not needed as for example 1 means ON and 0 means OFF
        "ON",
        "OFF",
        "TRUE",
        "FALSE",
        "YES", 
        "NO",
        "DELETE",
        "PERSIST",
        "MEMORY",
        "WAL",
        "TRUNCATE",
        "NORMAL",
        "FULL",
        "NONE",
        "EXCLUSIVE",
        "DEFAULT",
        "RESET"
      ],

      # Add all supported function names
      "<function_name>": [
        # Core scalar functions
        "abs", "changes", "char", "coalesce", "concat", "concat_ws", "format", 
        "glob", "hex", "ifnull", "iif", "instr", "last_insert_rowid", "length",
        "like", "likelihood", "likely", "load_extension", "lower", "ltrim",
        "max", "min", "nullif", "octet_length", "printf", "quote", "random",
        "randomblob", "replace", "round", "rtrim", "sign", "soundex", 
        "sqlite_compileoption_get", "sqlite_compileoption_used", 
        "sqlite_offset", "sqlite_source_id", "sqlite_version",
        "substr", "substring", "total_changes", "trim", "typeof", 
        "unicode", "unlikely", "upper", "zeroblob",
        
        # Date and time functions
        "date", "time", "datetime", "julianday", "strftime", "unixepoch", "timediff",
        
        # Math functions (require SQLITE_ENABLE_MATH_FUNCTIONS)
        "acos", "acosh", "asin", "asinh", "atan", "atan2", "atanh", 
        "ceil", "ceiling", "cos", "cosh", "degrees", "exp", "floor", 
        "ln", "log", "log10", "log2", "mod", "pi", "pow", "power",
        "radians", "sin", "sinh", "sqrt", "tan", "tanh", "trunc",
        
        # JSON functions
        "json", "json_array", "json_array_length", "json_extract", "json_insert",
        "json_object", "json_patch", "json_remove", "json_replace", "json_set",
        "json_type", "json_valid", "json_quote", "json_group_array", 
        "json_group_object", "json_each", "json_tree", "jsonb", "jsonb_array", 
        "jsonb_array_length", "jsonb_extract", "jsonb_insert", "jsonb_object", 
        "jsonb_patch", "jsonb_remove", "jsonb_replace", "jsonb_set", "jsonb_type", 
        "jsonb_valid", "jsonb_quote", "jsonb_group_array", "jsonb_group_object",
        
        # Aggregate functions
        "avg", "count", "group_concat", "max", "min", "string_agg", "sum", "total",
        
        # Window functions
        "row_number", "rank", "dense_rank", "percent_rank", "cume_dist", 
        "ntile", "lag", "lead", "first_value", "last_value", "nth_value"
      ],

      # Add all supported table function names
      "<table_function_name>": [
        # JSON table functions
        "json_each",
        "json_tree",
        "jsonb_each",
        "jsonb_tree",
        
        # SQLite pragma table functions
        "pragma_function_list",
        "pragma_module_list",
        "pragma_table_list",
        "pragma_table_info",
        "pragma_table_xinfo",
        "pragma_index_list",
        "pragma_index_info",
        "pragma_index_xinfo",
        "pragma_foreign_key_list",
        "pragma_collation_list",
        "pragma_compile_options",
        
        # Utility table functions
        "generate_series",
        "carray",
        
        # FTS virtual tables (when enabled)
        "fts3aux",
        "fts4aux",
        "fts5vocab",
        
        # RTrees (when enabled)
        "rtreenode",
        "rtreeproper"
      ],

      # Add all supported module names
      "<module_name>": [
        # Full-text search modules
        "fts3",
        "fts4",
        "fts5",
        
        # R-Tree modules for spatial indexing
        "rtree",
        "rtree_i32",
        
        # JSON modules
        "json",
        "json1",
        
        # CSV and structured data
        "csv",
        "carray",
        
        # Geographic modules
        "geopoly",
        
        # Series and numbers
        "series",
        "generate_series",
        "wholenumber",
        
        # Archive modules
        "zipfile",
        
        # Spell checking
        "spellfix1",
        
        # Autocompletion
        "completion",
        
        # Other utility modules
        "unionvtab",
        "swarmvtab",
        "dbstat",
        "memvfs",
        "zorder"
      ],

      # Set <any_name> to the correct name based on <h32>
      # Previously:
      # "<drop_stmt>": ["<DROP_> <h32> <symbol-46-1> <symbol-47-1> <any_name>"],
      # "<h32>": ["<INDEX_>", "<TABLE_>", "<TRIGGER_>", "<VIEW_>"],
      "<drop_stmt>": [
          "<DROP_> <INDEX_> <symbol-46-1> <symbol-47-1> <index_name>",
          "<DROP_> <TABLE_> <symbol-46-1> <symbol-47-1> <table_name>",
          "<DROP_> <TRIGGER_> <symbol-46-1> <symbol-47-1> <trigger_name>",
          "<DROP_> <VIEW_> <symbol-46-1> <symbol-47-1> <view_name>",
      ],
          
      # Enforce LIMIT to be followed by DIGIT
      "<limit_stmt>": ["<LIMIT_> <DIGIT>"],

      # Remove ORDER BY statement
      "<order_by_stmt-1>": [""],
      "<order_by_stmt-2>": [""],
      "<order_by_stmt-3>": [""],
      "<order_by_stmt-4>": [""],
      "<order_by_stmt-5>": [""],

      # Before the first expansion, decide randomly for a table to choose the names from
      "<parse>": [("<sql_stmt_list>", opts(pre=select_random_table))],

      # NOTE: If <table_name> is used in a <create_table_stmt>, we try to create a table with a name that already exists
      # This issue also exists with other names like <column_name> when for example inserting an existing column
      "<table_name>": [
          ("<any_name>",
           opts(pre=lambda: use_name('table_name'))
          )
      ],
      "<column_name>": [
          ("<any_name>",
           opts(pre=lambda: use_name('column_name'))
          )
      ],
      "<table_or_index_name>": [
          ("<any_name>",
           opts(pre=lambda: use_name('table_name') or use_name('index_name') or None)
          )
      ],
      "<index_name>": [
          ("<any_name>",
           opts(pre=lambda: use_name('index_name'))
          )
      ],
      "<foreign_table>": [
          ("<any_name>",
           opts(pre=lambda: use_name('table_name')) # Intentionally the same as <table_name>
          )
      ]
      # "<savepoint_name>": [
      #     ("<any_name>",
      #      opts(pre=lambda: use_name('savepoint_name'))
      #     )
      # ],
      # "<collation_name>": [
      #     ("<any_name>",
      #      opts(pre=lambda: use_name('collation_name'))
      #     )
      # ],
      # "<trigger_name>": [
      #     ("<any_name>",
      #      opts(pre=lambda: use_name('trigger_name'))
      #     )
      # ],
      # "<view_name>": [
      #     ("<any_name>",
      #      opts(pre=lambda: use_name('view_name'))
      #     )
      # ],
      # "<window_name>": [
      #     ("<any_name>",
      #      opts(pre=lambda: use_name('window_name'))
      #     )
      # ],
      # "<base_window_name>": [
      #     ("<any_name>",
      #      opts(pre=lambda: use_name('window_name')) # Intentionally the same as <window_name>
      #     )
      # ]
  }
)
