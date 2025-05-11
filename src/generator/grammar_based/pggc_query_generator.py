import copy
from typing import List, Set

from generator.grammar_based.pre_post_grammar_query_generator import PrePostGrammarQueryGenerator
from generator.grammar_based.probabilistic_coverage_grammar_query_generator import ProbabilisticCoverageGrammarQueryGenerator

from generator.grammar_based.utils.grammar import Grammar

from generator.grammar_based.utils.derivation_tree import DerivationTree


class PGGCQueryGenerator(PrePostGrammarQueryGenerator, ProbabilisticCoverageGrammarQueryGenerator):
    """Probabilistic Generative Grammar- and Coverage-based Query Generator.
    Joins the features of PrePostGrammarQueryGenerator and ProbabilisticCoverageGrammarQueryGenerator.
    """
    
    def supported_opts(self) -> Set[str]:
        return (super(PrePostGrammarQueryGenerator, self).supported_opts() |
                super(ProbabilisticCoverageGrammarQueryGenerator, self).supported_opts())
    
    def __init__(self, grammar: Grammar, *,
                 start_symbol="<start>",
                 replacement_attempts: int = 10, 
                 **kwargs) -> None:
        """Constructor.
        `replacement_attempts` - see `PrePostGrammarQueryGenerator` constructor.
        All other keywords go into `ProbabilisticCoverageGrammarQueryGenerator`.
        """
        PrePostGrammarQueryGenerator.__init__(
            self,
            grammar,
            start_symbol=start_symbol,  # Pass start_symbol explicitly
            replacement_attempts=replacement_attempts
        )
        
        ProbabilisticCoverageGrammarQueryGenerator.__init__(
            self,
            grammar,
            start_symbol=start_symbol,  # Pass start_symbol explicitly
            **kwargs
        )
    
    # Rest of the class remains the same
    def fuzz_tree(self) -> DerivationTree:
        self.orig_covered_expansions = copy.deepcopy(self.covered_expansions)
        tree = super().fuzz_tree()
        self.covered_expansions = self.orig_covered_expansions
        self.add_tree_coverage(tree)
        return tree
    
    def add_tree_coverage(self, tree: DerivationTree) -> None:
        (symbol, children) = tree
        assert isinstance(children, list)
        if len(children) > 0:
            flat_children: List[DerivationTree] = [
                (child_symbol, None)
                for (child_symbol, _) in children
            ]
            self.add_coverage(symbol, flat_children)
            for c in children:
                self.add_tree_coverage(c)
    
    def restart_expansion(self) -> None:
        super().restart_expansion()
        self.covered_expansions = self.orig_covered_expansions
        