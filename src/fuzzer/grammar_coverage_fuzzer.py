import random
from typing import Union, Set, Optional, List

from fuzzer.grammar_fuzzer import GrammarFuzzer

from utils. derivation_tree import DerivationTree, expansion_key, Expansion

from utils.grammar import START_SYMBOL, nonterminals

class GrammarCoverageFuzzer(GrammarFuzzer):
    """Produce from grammars, aiming for coverage of all expansions."""

    def __init__(self, *args, **kwargs) -> None:
        # invoke superclass __init__(), passing all arguments
        super().__init__(*args, **kwargs)
        self.reset_coverage()

    def expansion_coverage(self) -> Set[str]:
        """Return the set of covered expansions as strings SYMBOL -> EXPANSION"""
        return self.covered_expansions

    def reset_coverage(self) -> None:
        """Clear coverage info tracked so far"""
        self.covered_expansions: Set[str] = set()

    def _max_expansion_coverage(self, symbol: str, 
                                max_depth: Union[int, float]) -> Set[str]:
        if max_depth <= 0:
            return set()

        self._symbols_seen.add(symbol)

        expansions = set()
        for expansion in self.grammar[symbol]:
            expansions.add(expansion_key(symbol, expansion))
            for nonterminal in nonterminals(expansion):
                if nonterminal not in self._symbols_seen:
                    expansions |= self._max_expansion_coverage(
                        nonterminal, max_depth - 1)

        return expansions

    def max_expansion_coverage(self, symbol: Optional[str] = None,
                               max_depth: Union[int, float] = float('inf')) \
            -> Set[str]:
        """Return set of all expansions in a grammar 
           starting with `symbol` (default: start symbol).
           If `max_depth` is given, expand only to that depth."""
        if symbol is None:
            symbol = self.start_symbol

        self._symbols_seen: Set[str] = set()
        cov = self._max_expansion_coverage(symbol, max_depth)

        if symbol == START_SYMBOL:
            assert len(self._symbols_seen) == len(self.grammar)

        return cov
    
    def add_coverage(self, symbol: str,
                     new_child: Union[Expansion, List[DerivationTree]]) -> None:
        key = expansion_key(symbol, new_child)

        if self.log and key not in self.covered_expansions:
            print("Now covered:", key)
        self.covered_expansions.add(key)

    def choose_node_expansion(self, node: DerivationTree,
                              children_alternatives: List[List[DerivationTree]]) -> int:
        """Choose an expansion of `node` among `children_alternatives`.
           Return `n` such that expanding `children_alternatives[n]`
           yields the highest additional coverage."""

        (symbol, children) = node
        new_coverages = self.new_coverages(node, children_alternatives)

        if new_coverages is None:
            # All expansions covered - use superclass method
            return self.choose_covered_node_expansion(node, children_alternatives)

        max_new_coverage = max(len(cov) for cov in new_coverages)

        children_with_max_new_coverage = [c for (i, c) in enumerate(children_alternatives)
                                          if len(new_coverages[i]) == max_new_coverage]
        index_map = [i for (i, c) in enumerate(children_alternatives)
                     if len(new_coverages[i]) == max_new_coverage]

        # Select a random expansion
        new_children_index = self.choose_uncovered_node_expansion(
            node, children_with_max_new_coverage)
        new_children = children_with_max_new_coverage[new_children_index]

        # Save the expansion as covered
        key = expansion_key(symbol, new_children)

        if self.log:
            print("Now covered:", key)
        self.covered_expansions.add(key)

        return index_map[new_children_index]
    
    def missing_expansion_coverage(self) -> Set[str]:
        """Return expansions not covered yet"""
        return self.max_expansion_coverage() - self.expansion_coverage()
    
    def choose_uncovered_node_expansion(self,
                                        node: DerivationTree,
                                        children_alternatives: List[List[DerivationTree]]) -> int:
        """Return index of expansion in _uncovered_ `children_alternatives`
           to be selected."""
        
        (symbol, children) = node
        index = super().choose_node_expansion(node, children_alternatives)
        self.add_coverage(symbol, children_alternatives[index])
        return index

    def choose_covered_node_expansion(self,
                                      node: DerivationTree,
                                      children_alternatives: List[List[DerivationTree]]) -> int:
        """Return index of expansion in _covered_ `children_alternatives`
           to be selected."""
        (symbol, children) = node
        index = super().choose_node_expansion(node, children_alternatives)
        self.add_coverage(symbol, children_alternatives[index])
        return index
    
    def new_child_coverage(self,
                           symbol: str,
                           children: List[DerivationTree],
                           max_depth: Union[int, float] = float('inf')) -> Set[str]:
        """Return new coverage that would be obtained 
           by expanding (`symbol`, `children`)"""

        new_cov = self._new_child_coverage(children, max_depth)
        new_cov.add(expansion_key(symbol, children))
        new_cov -= self.expansion_coverage()   # -= is set subtraction
        return new_cov

    def _new_child_coverage(self, children: List[DerivationTree],
                            max_depth: Union[int, float]) -> Set[str]:
        new_cov: Set[str] = set()
        for (c_symbol, _) in children:
            if c_symbol in self.grammar:
                new_cov |= self.max_expansion_coverage(c_symbol, max_depth)

        return new_cov
    
    def new_coverages(self, node: DerivationTree,
                      children_alternatives: List[List[DerivationTree]]) \
            -> Optional[List[Set[str]]]:
        """Return coverage to be obtained for each child at minimum depth"""

        (symbol, children) = node
        for max_depth in range(len(self.grammar)):
            new_coverages = [
                self.new_child_coverage(
                    symbol, c, max_depth) for c in children_alternatives]
            max_new_coverage = max(len(new_coverage)
                                   for new_coverage in new_coverages)
            if max_new_coverage > 0:
                # Uncovered node found
                return new_coverages

        # All covered
        return None
    
    