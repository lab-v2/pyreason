import pyreason.scripts.utils.rule_parser as rule_parser


class Rule:
    """
    Example text:
            `'pred1(x,y) : [0.2, 1] <- pred2(a, b) : [1,1], pred3(b, c)'`

    1. It is not possible to specify thresholds. Threshold is greater than or equal to 1 by default
    2. It is not possible to have weights for different clauses. Weights are 1 by default with bias 0
    TODO: Add threshold class where we can pass this as a parameter
    TODO: Add weights as a parameter
    """
    def __init__(self, rule_text: str, name: str, infer_edges: bool = False, set_static: bool = False, immediate_rule: bool = False):
        """
        :param rule_text: The rule in text format
        :param name: The name of the rule. This will appear in the rule trace
        :param infer_edges: Whether to infer new edges after edge rule fires
        :param set_static: Whether to set the atom in the head as static if the rule fires. The bounds will no longer change
        :param immediate_rule: Whether the rule is immediate. Immediate rules check for more applicable rules immediately after being applied
        """
        self.rule = rule_parser.parse_rule(rule_text, name, infer_edges, set_static, immediate_rule)
