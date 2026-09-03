# Example: the forall() quantifier in rule bodies.
#
# forall(clause) is shorthand for a custom threshold of
# Threshold("greater_equal", ("percent", "total"), 100) on that clause:
# the rule only fires when ALL groundings of the clause are satisfied.
#
# This is the group-chat example from the custom thresholds tutorial,
# rewritten without any explicit Threshold objects. A text message is
# ViewedByAll only once every person with access to it has viewed it.
import networkx as nx
import pyreason as pr

# Use a directed graph: undirected edges are loaded as two directed edges,
# which doubles the groundings that percent thresholds count.
G = nx.DiGraph()
G.add_nodes_from(["TextMessage", "Zach", "Justin", "Michelle", "Amy"])
G.add_edges_from([
    ("Zach", "TextMessage", {"HaveAccess": 1}),
    ("Justin", "TextMessage", {"HaveAccess": 1}),
    ("Michelle", "TextMessage", {"HaveAccess": 1}),
    ("Amy", "TextMessage", {"HaveAccess": 1}),
])

pr.reset()
pr.reset_rules()
pr.settings.verbose = False
pr.load_graph(G)

# Equivalent to passing:
#   custom_thresholds=[
#       pr.Threshold("greater_equal", ("number", "total"), 1),
#       pr.Threshold("greater_equal", ("percent", "total"), 100),
#   ]
# with the rule text "ViewedByAll(y) <- HaveAccess(x,y), Viewed(x)"
pr.add_rule(pr.Rule(
    "ViewedByAll(y) <- HaveAccess(x,y), forall(Viewed(x))",
    "viewed_by_all_rule",
))

# Zach and Justin view the message at t=0, Michelle at t=1, Amy at t=2
pr.add_fact(pr.Fact("Viewed(Zach)", "seen-fact-zach", 0, 3))
pr.add_fact(pr.Fact("Viewed(Justin)", "seen-fact-justin", 0, 3))
pr.add_fact(pr.Fact("Viewed(Michelle)", "seen-fact-michelle", 1, 3))
pr.add_fact(pr.Fact("Viewed(Amy)", "seen-fact-amy", 2, 3))

interpretation = pr.reason(timesteps=3)

# ViewedByAll(TextMessage) should first appear at t=2, when the last
# person (Amy) views the message.
dataframes = pr.filter_and_sort_nodes(interpretation, ["ViewedByAll"])
for t, df in enumerate(dataframes):
    print(f"TIMESTEP - {t}")
    print(df)
    print()
