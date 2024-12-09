import pyreason.scripts.utils.rule_parser as rule_parser


class Rule:
    """
    Example text:
            `'pred1(x,y) : [0.2, 1] <- pred2(a, b) : [1,1], pred3(b, c)'`

    1. It is not possible to have weights for different clauses. Weights are 1 by default with bias 0
    """
    def __init__(self, rule_text: str, name: str = None, infer_edges: bool = False, set_static: bool = False, custom_thresholds=None, weights=None):
        """
        :param rule_text: The rule in text format
        :param name: The name of the rule. This will appear in the rule trace
        :param infer_edges: Whether to infer new edges after edge rule fires
        :param set_static: Whether to set the atom in the head as static if the rule fires. The bounds will no longer change
        :param custom_thresholds: A list of custom thresholds for the rule. If not specified, the default thresholds for ANY are used. It can be a list of
               size #of clauses or a map of clause index to threshold
        :param weights: A list of weights for the rule clauses. This is passed to an annotation function. If not specified,
               the weights array is a list of 1s with the length as number of clauses.
        """
        self.rule = rule_parser.parse_rule(rule_text, name, custom_thresholds, infer_edges, set_static, weights)
