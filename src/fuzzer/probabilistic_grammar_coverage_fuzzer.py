from fuzzer.grammar_coverage_fuzzer import GrammarCoverageFuzzer
from fuzzer.probabilistic_grammar_fuzzer import ProbabilisticGrammarFuzzer

class ProbabilisticGrammarCoverageFuzzer(
        GrammarCoverageFuzzer, ProbabilisticGrammarFuzzer):
    # Choose uncovered expansions first
    def choose_node_expansion(self, node, children_alternatives):
        return GrammarCoverageFuzzer.choose_node_expansion(
            self, node, children_alternatives)

    # Among uncovered expansions, pick by (relative) probability
    def choose_uncovered_node_expansion(self, node, children_alternatives):
        return ProbabilisticGrammarFuzzer.choose_node_expansion(
            self, node, children_alternatives)

    # For covered nodes, pick by probability, too
    def choose_covered_node_expansion(self, node, children_alternatives):
        return ProbabilisticGrammarFuzzer.choose_node_expansion(
            self, node, children_alternatives)
    