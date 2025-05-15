from typing import Union, Set, Optional, List

from generator.grammar_based.grammar_query_generator import GrammarQueryGenerator

from generator.grammar_based.utils.derivation_tree import DerivationTree, expansion_key, Expansion

from generator.grammar_based.utils.grammar import START_SYMBOL, nonterminals

class CoverageGrammarQueryGenerator(GrammarQueryGenerator):
    """Produce from grammars, aiming for coverage of all expansions."""

    def __init__(self, *args, **kwargs) -> None:
        # invoke superclass __init__(), passing all arguments
        super().__init__(*args, **kwargs)
        
        # Initialize caches
        self._max_expansion_cache = {}
        self._new_child_coverage_cache = {}
        self._new_coverages_cache = {}
        
        # For tracking overall grammar coverage
        self.grammar_coverage = 0.0
        
        # Complete set of grammar expansions (calculated once)
        self._all_grammar_expansions = None
        
        self.reset_coverage()

    def expansion_coverage(self) -> Set[str]:
        """Return the set of covered expansions as strings SYMBOL -> EXPANSION"""
        return self.covered_expansions

    def reset_coverage(self) -> None:
        """Clear coverage info tracked so far"""
        self.covered_expansions: Set[str] = set()
        
        # Clear caches related to coverage progression
        self._new_child_coverage_cache = {}
        self._new_coverages_cache = {}
        
        # Reset coverage percentage
        self.grammar_coverage = 0.0

    def _max_expansion_coverage(self, symbol: str, 
                                max_depth: Union[int, float]) -> Set[str]:
        """Calculate maximum coverage for a symbol with caching"""
        # Try to use cache
        cache_key = (symbol, max_depth)
        if cache_key in self._max_expansion_cache:
            return self._max_expansion_cache[cache_key].copy()
            
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

        # Cache the result
        self._max_expansion_cache[cache_key] = expansions.copy()
        return expansions

    def max_expansion_coverage(self, symbol: Optional[str] = None,
                               max_depth: Union[int, float] = float('inf')) \
            -> Set[str]:
        """Return set of all expansions in a grammar 
           starting with `symbol` (default: start symbol).
           If `max_depth` is given, expand only to that depth."""
        
        # For full grammar coverage (common case)
        if symbol is None and max_depth == float('inf'):
            # Calculate once and cache
            if self._all_grammar_expansions is None:
                symbol = self.start_symbol
                self._symbols_seen = set()
                self._all_grammar_expansions = self._max_expansion_coverage(symbol, max_depth)
                
                if symbol == START_SYMBOL:
                    assert len(self._symbols_seen) == len(self.grammar)
            
            return self._all_grammar_expansions.copy()
        
        # For other cases (partial coverage)
        if symbol is None:
            symbol = self.start_symbol

        self._symbols_seen = set()
        cov = self._max_expansion_coverage(symbol, max_depth)

        if symbol == START_SYMBOL:
            assert len(self._symbols_seen) == len(self.grammar)

        return cov
    
    def add_coverage(self, symbol: str,
                     new_child: Union[Expansion, List[DerivationTree]]) -> None:
        """Add an expansion to the covered set and update grammar coverage"""
        key = expansion_key(symbol, new_child)

        if self.log and key not in self.covered_expansions:
            print("Now covered:", key)
        
        # Add to covered set
        self.covered_expansions.add(key)
        
        # Update grammar coverage percentage
        if self._all_grammar_expansions is None:
            self.max_expansion_coverage()  # Calculate all expansions if needed
        
        if self._all_grammar_expansions:
            # Only count valid expansions for coverage percentage
            valid_covered = self.covered_expansions.intersection(self._all_grammar_expansions)
            self.grammar_coverage = (len(valid_covered) * 100.0) / len(self._all_grammar_expansions)

    def choose_node_expansion(self, node: DerivationTree,
                              children_alternatives: List[List[DerivationTree]]) -> int:
        """Choose an expansion of `node` among `children_alternatives`.
           Return `n` such that expanding `children_alternatives[n]`
           yields the highest additional coverage."""
        
        # Periodically clean caches if they get too large
        import random
        if random.random() < 0.01:  # 1% chance to clean caches
            if len(self._new_child_coverage_cache) > 10000:
                self._new_child_coverage_cache = {}
            if len(self._new_coverages_cache) > 5000:
                self._new_coverages_cache = {}

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
        self.add_coverage(symbol, new_children)

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
           by expanding (`symbol`, `children`) with caching"""
        
        # Try to use cache
        try:
            # Create a stable key for caching
            children_key = tuple((c[0], str(c[1])[:50] if c[1] else None) for c in children)
            cache_key = (symbol, children_key, max_depth)
            
            if cache_key in self._new_child_coverage_cache:
                return self._new_child_coverage_cache[cache_key].copy()
        except:
            # If we can't create a stable key, proceed without caching
            pass

        # Compute the new coverage
        new_cov = self._new_child_coverage(children, max_depth)
        new_cov.add(expansion_key(symbol, children))
        new_cov -= self.expansion_coverage()   # -= is set subtraction
        
        # Cache the result
        try:
            if 'cache_key' in locals():
                self._new_child_coverage_cache[cache_key] = new_cov.copy()
        except:
            pass
            
        return new_cov

    def _new_child_coverage(self, children: List[DerivationTree],
                            max_depth: Union[int, float]) -> Set[str]:
        """Get coverage from child nodes with caching"""
        new_cov: Set[str] = set()
        for (c_symbol, _) in children:
            if c_symbol in self.grammar:
                new_cov |= self.max_expansion_coverage(c_symbol, max_depth)

        return new_cov
    
    def new_coverages(self, node: DerivationTree,
                      children_alternatives: List[List[DerivationTree]]) \
            -> Optional[List[Set[str]]]:
        """Return coverage to be obtained for each child at minimum depth with caching"""
        
        # Try to use cache
        try:
            node_key = (node[0], str(node[1])[:50] if node[1] else None)
            cache_key = (node_key, len(children_alternatives))
            
            if cache_key in self._new_coverages_cache:
                return self._new_coverages_cache[cache_key]
        except:
            # If we can't create a stable key, proceed without caching
            pass
        
        # Original computation
        (symbol, children) = node
        for max_depth in range(len(self.grammar)):
            new_coverages = [
                self.new_child_coverage(
                    symbol, c, max_depth) for c in children_alternatives]
            max_new_coverage = max(len(new_coverage)
                                   for new_coverage in new_coverages)
            if max_new_coverage > 0:
                # Uncovered node found
                
                # Cache the result
                try:
                    if 'cache_key' in locals():
                        self._new_coverages_cache[cache_key] = new_coverages
                except:
                    pass
                    
                return new_coverages

        # All covered
        return None
        
    def get_grammar_coverage_percentage(self) -> float:
        """Get current grammar coverage percentage"""
        return self.grammar_coverage
    