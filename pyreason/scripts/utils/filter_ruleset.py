def filter_ruleset(queries, rules):
    """
    Filter the ruleset based on the queries provided.

    :param queries: List of Query objects
    :param rules: List of Rule objects
    :return: List of Rule objects that are applicable to the queries
    """

    # Helper function to collect all rules that can support making a given rule true
    def applicable_rules_from_query(query):
        # Start with rules that match the query directly
        applicable = []

        for rule in rules:
            # If the rule's target matches the query
            if query == rule.get_target():
                # Add the rule to the applicable set
                applicable.append(rule)
                # Recursively check rules that can lead up to this rule
                for clause in rule.get_clauses():
                    # Find supporting rules with the clause as the target
                    supporting_rules = applicable_rules_from_query(clause[1])
                    applicable.extend(supporting_rules)

        return applicable

    # Collect applicable rules for each query and eliminate duplicates
    filtered_rules = []
    for q in queries:
        filtered_rules.extend(applicable_rules_from_query(q.get_predicate()))

    # Use set to avoid duplicates if a rule supports multiple queries
    return list(set(filtered_rules))
