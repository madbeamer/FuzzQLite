import copy
from typing import List, Set

from fuzzer.generator_grammar_fuzzer import GeneratorGrammarFuzzer
from fuzzer.probabilistic_grammar_coverage_fuzzer import ProbabilisticGrammarCoverageFuzzer

from utils.grammar import Grammar

from utils.derivation_tree import DerivationTree


class PGGCFuzzer(GeneratorGrammarFuzzer, ProbabilisticGrammarCoverageFuzzer):
    """Probabilistic Generative Grammar- and Coverage-based Fuzzer.
    Joins the features of GeneratorGrammarFuzzer and ProbabilisticGrammarCoverageFuzzer.
    """
    
    def supported_opts(self) -> Set[str]:
        return (super(GeneratorGrammarFuzzer, self).supported_opts() |
                super(ProbabilisticGrammarCoverageFuzzer, self).supported_opts())
    
    def __init__(self, grammar: Grammar, *,
                 start_symbol="<start>",  # Add this parameter explicitly
                 replacement_attempts: int = 11, 
                 **kwargs) -> None:
        """Constructor.
        `replacement_attempts` - see `GeneratorGrammarFuzzer` constructor.
        All other keywords go into `ProbabilisticGrammarFuzzer`.
        """
        # Initialize GeneratorGrammarFuzzer with correct parameters
        GeneratorGrammarFuzzer.__init__(
            self,
            grammar,
            start_symbol=start_symbol,  # Pass start_symbol explicitly
            replacement_attempts=replacement_attempts
        )
        
        # Initialize ProbabilisticGrammarCoverageFuzzer
        ProbabilisticGrammarCoverageFuzzer.__init__(
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
        