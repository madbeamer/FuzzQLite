from generator.grammar_based.coverage_grammar_query_generator import CoverageGrammarQueryGenerator
from generator.grammar_based.probabilistic_grammar_query_generator import ProbabilisticGrammarQueryGenerator

class ProbabilisticCoverageGrammarQueryGenerator(
        CoverageGrammarQueryGenerator, ProbabilisticGrammarQueryGenerator):
    # Choose uncovered expansions first
    def choose_node_expansion(self, node, children_alternatives):
        return CoverageGrammarQueryGenerator.choose_node_expansion(
            self, node, children_alternatives)

    # Among uncovered expansions, pick by (relative) probability
    def choose_uncovered_node_expansion(self, node, children_alternatives):
        return ProbabilisticGrammarQueryGenerator.choose_node_expansion(
            self, node, children_alternatives)

    # For covered nodes, pick by probability, too
    def choose_covered_node_expansion(self, node, children_alternatives):
        return ProbabilisticGrammarQueryGenerator.choose_node_expansion(
            self, node, children_alternatives)
    