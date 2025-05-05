import codecs
import re
import string
from typing import List, Tuple, Optional, Any, Callable, Dict
from graphviz import Digraph

from utils.grammar import is_nonterminal


DerivationTree = Tuple[str, Optional[List[Any]]]

# Core functionality of the derivation tree
def all_terminals(tree: DerivationTree) -> str:
    (symbol, children) = tree
    if children is None:
        # This is a nonterminal symbol not expanded yet
        return symbol

    if len(children) == 0:
        # This is a terminal symbol
        return symbol

    # This is an expanded symbol:
    # Concatenate all terminal symbols from all children
    return ''.join([all_terminals(c) for c in children])

def tree_to_string(tree: DerivationTree) -> str:
    symbol, children, *_ = tree
    if children:
        return ''.join(tree_to_string(c) for c in children)
    else:
        return '' if is_nonterminal(symbol) else symbol

# Visualization of derivation trees
def dot_escape(s: str, show_ascii=None) -> str:
    """Return s in a form suitable for dot.
    If `show_ascii` is True or length of `s` is 1, also append ascii value."""
    escaped_s = ''
    if show_ascii is None:
        show_ascii = (len(s) == 1)  # Default: Single chars only

    if show_ascii and s == '\n':
        return '\\\\n (10)'

    s = s.replace('\n', '\\n')
    for c in s:
        if re.match('[,<>\\\\"]', c):
            escaped_s += '\\' + c
        elif c in string.printable and 31 < ord(c) < 127:
            escaped_s += c
        else:
            escaped_s += '\\\\x' + format(ord(c), '02x')

        if show_ascii:
            escaped_s += f' ({ord(c)})'

    return escaped_s

def extract_node(node, id):
    symbol, children, *annotation = node
    return symbol, children, ''.join(str(a) for a in annotation)

def default_node_attr(dot, nid, symbol, ann):
    dot.node(repr(nid), dot_escape(symbol))

def default_edge_attr(dot, start_node, stop_node):
    dot.edge(repr(start_node), repr(stop_node))

def default_graph_attr(dot):
    dot.attr('node', shape='plain')

def display_tree(derivation_tree: DerivationTree,
                 log: bool = False,
                 extract_node: Callable = extract_node,
                 node_attr: Callable = default_node_attr,
                 edge_attr: Callable = default_edge_attr,
                 graph_attr: Callable = default_graph_attr) -> Any:

    counter = 0

    def traverse_tree(dot, tree, id=0):
        (symbol, children, annotation) = extract_node(tree, id)
        node_attr(dot, id, symbol, annotation)

        if children:
            for child in children:
                nonlocal counter
                counter += 1
                child_id = counter
                edge_attr(dot, id, child_id)
                traverse_tree(dot, child, child_id)

    dot = Digraph(comment="Derivation Tree")
    graph_attr(dot)
    traverse_tree(dot, derivation_tree)
    if log:
        print(dot)
    return dot

def display_annotated_tree(tree: DerivationTree,
                           a_nodes: Dict[int, str],
                           a_edges: Dict[Tuple[int, int], str],
                           log: bool = False):
    def graph_attr(dot):
        dot.attr('node', shape='plain')
        dot.graph_attr['rankdir'] = 'LR'

    def annotate_node(dot, nid, symbol, ann):
        if nid in a_nodes:
            dot.node(repr(nid), 
                     "%s (%s)" % (dot_escape(dot_escape(codecs.decode(symbol, 'unicode_escape'))),
                                  a_nodes[nid]))
        else:
            dot.node(repr(nid), dot_escape(dot_escape(codecs.decode(symbol, 'unicode_escape'))))

    def annotate_edge(dot, start_node, stop_node):
        if (start_node, stop_node) in a_edges:
            dot.edge(repr(start_node), repr(stop_node),
                     a_edges[(start_node, stop_node)])
        else:
            dot.edge(repr(start_node), repr(stop_node))

    return display_tree(tree, log=log,
                        node_attr=annotate_node,
                        edge_attr=annotate_edge,
                        graph_attr=graph_attr)
