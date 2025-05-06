import random
from typing import List, Dict, Optional, Set, cast, Any

from fuzzer.grammar_fuzzer import GrammarFuzzer

from utils.grammar import Grammar, Expansion, exp_opt, exp_string, is_valid_grammar, START_SYMBOL

from utils.derivation_tree import DerivationTree, all_terminals

def exp_prob(expansion: Expansion) -> float:
    """Return the options of an expansion"""
    return exp_opt(expansion, 'prob')

def exp_probabilities(expansions: List[Expansion],
                      nonterminal: str ="<symbol>") \
        -> Dict[Expansion, float]:
    probabilities = [exp_prob(expansion) for expansion in expansions]
    prob_dist = prob_distribution(probabilities, nonterminal)

    prob_mapping: Dict[Expansion, float] = {}
    for i in range(len(expansions)):
        expansion = exp_string(expansions[i])
        prob_mapping[expansion] = prob_dist[i]

    return prob_mapping

def prob_distribution(probabilities: List[Optional[float]],
                      nonterminal: str = "<symbol>"):
    epsilon = 0.00001

    number_of_unspecified_probabilities = probabilities.count(None)
    if number_of_unspecified_probabilities == 0:
        sum_probabilities = cast(float, sum(probabilities))
        assert abs(sum_probabilities - 1.0) < epsilon, \
            nonterminal + ": sum of probabilities must be 1.0"
        return probabilities

    sum_of_specified_probabilities = 0.0
    for p in probabilities:
        if p is not None:
            sum_of_specified_probabilities += p
    assert 0 <= sum_of_specified_probabilities <= 1.0, \
        nonterminal + ": sum of specified probabilities must be between 0.0 and 1.0"

    default_probability = ((1.0 - sum_of_specified_probabilities)
                           / number_of_unspecified_probabilities)
    all_probabilities = []
    for p in probabilities:
        if p is None:
            p = default_probability
        all_probabilities.append(p)

    assert abs(sum(all_probabilities) - 1.0) < epsilon
    return all_probabilities

def is_valid_probabilistic_grammar(grammar: Grammar,
                                   start_symbol: str = START_SYMBOL) -> bool:
    if not is_valid_grammar(grammar, start_symbol):
        return False

    for nonterminal in grammar:
        expansions = grammar[nonterminal]
        _ = exp_probabilities(expansions, nonterminal)

    return True


class ProbabilisticGrammarFuzzer(GrammarFuzzer):
    """A grammar-based fuzzer respecting probabilities in grammars."""

    def check_grammar(self) -> None:
        super().check_grammar()
        assert is_valid_probabilistic_grammar(self.grammar, self.start_symbol)

    def supported_opts(self) -> Set[str]:
        return super().supported_opts() | {'prob'}
    
    def choose_node_expansion(self, node: DerivationTree,
                              children_alternatives: List[Any]) -> int:
        (symbol, tree) = node
        expansions = self.grammar[symbol]
        probabilities = exp_probabilities(expansions)

        weights: List[float] = []
        for children in children_alternatives:
            expansion = all_terminals((symbol, children))
            children_weight = probabilities[expansion]
            if self.log:
                print(repr(expansion), "p =", children_weight)
            weights.append(children_weight)

        if sum(weights) == 0:
            # No alternative (probably expanding at minimum cost)
            return random.choices(
                range(len(children_alternatives)))[0]
        else:
            return random.choices(
                range(len(children_alternatives)), weights=weights)[0]
        