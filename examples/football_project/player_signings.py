import numba
import pyreason as pr
import networkx as nx
import football_classes as fc
import random
from pprint import pprint
import matplotlib.pyplot as plt # type: ignore

# Generates random names
import names

def generate_random_player_at_position(position):
    full_name = names.get_full_name()
    name_with_underscore = full_name.replace(" ", "_")
    return fc.FootballPlayer(
        name=name_with_underscore,
        position=position,
        expected_salary=random.randint(100000, 500000),
        madden_rating=random.randint(60, 99),
    )

def add_rostered_fact(team, player):
    fact_string = f"rostered({team.team_name} , {player.name})"
    pr.add_fact(pr.Fact(fact_string, 'rostered_fact', 0, 1))

def add_not_rostered_fact(team, player):
    fact_string = f"~rostered({team.team_name} , {player.name})"
    pr.add_fact(pr.Fact(fact_string, 'rostered_fact', 0, 1))

def try_to_sign_player(team, player):
    if team.can_sign_player(player):
        team.sign_player(player)
        add_rostered_fact(team, player)
        print(f"{team.team_name} signed {player.name} for ${player.expected_salary}")
    else:
        add_not_rostered_fact(team, player)

# Operating at timestep 1 
def add_interested_fact(team, player):
    fact_string = f"interested({team.team_name} , {player.name})"
    pr.add_fact(pr.Fact(fact_string, 'interested_fact', 0, 1))

def add_not_interested_fact(team, player):
    fact_string = f"~interested({team.team_name} , {player.name})"
    pr.add_fact(pr.Fact(fact_string, 'interested_fact', 0, 1))

def determine_team_interest():
    for team in team_list:
        for player in all_player_list:
            if team.check_if_team_wants_players(player):
                add_interested_fact(team, player)
            else:
                add_not_interested_fact(team, player)

def simulate_draft():
    # print("Available Players:")
    # for player in all_players:
    #     print(f"Name: {player.name}, Position: {player.position}, "
    #           f"Expected Salary: ${player.expected_salary:,}, Madden Rating: {player.madden_rating}")
    for team in team_list:
        # Loop through the available players and try to sign them
        for player in qb_list:
            if team.get_num_player_needed("QB") > 0:
                try_to_sign_player(team, player)
            else:
                add_not_rostered_fact(team, player)
        for player in rb_list:
            if team.get_num_player_needed("RB") > 0:
                try_to_sign_player(team, player)
            else:
                add_not_rostered_fact(team, player)
        for player in wr_list:
            if team.get_num_player_needed("WR") > 0:
                try_to_sign_player(team, player)
            else:
                add_not_rostered_fact(team, player)
        for player in te_list:
            if team.get_num_player_needed("TE") > 0:
                try_to_sign_player(team, player)
            else:
                add_not_rostered_fact(team, player)

    # Print the final rosters and cap space for each team
    print("\nFinal Rosters and Cap Space:")
    for team in team_list:
        print(f"\n{team.team_name} Roster:")
        for position, players in team.roster.items():
            for player in players:
                print(f"  Name: {player.name}, Position: {player.position}, Value: {player.player_value}")
        print(f"Cap Space Remaining: ${team.get_cap_space():,}")


qb_list = []
rb_list = []
wr_list = []
te_list = []
all_player_list = []

for val in range(20):
    qb_list.append(generate_random_player_at_position("QB"))
    rb_list.append(generate_random_player_at_position("RB"))
    wr_list.append(generate_random_player_at_position("WR"))
    te_list.append(generate_random_player_at_position("TE"))

all_player_list.extend(qb_list)
all_player_list.extend(rb_list)
all_player_list.extend(wr_list)
all_player_list.extend(te_list)

team_list = []
team_list.append(fc.FootballTeam("Pittsburgh_Steelers"))
team_list.append(fc.FootballTeam("Baltamore_Ravens"))
team_list.append(fc.FootballTeam("Dallas_Cowboys"))
team_list.append(fc.FootballTeam("Chicago_Bears"))



# Create a Directed graph
g = nx.DiGraph()

for player in all_player_list:
    g.add_node(player.name, name=player.name, position=player.position, expected_salary=player.expected_salary, madden_rating=player.madden_rating, player_value=player.player_value)
for team in team_list:
    g.add_node(team.team_name)

# Make a picture of the graph
# nx.draw(g, with_labels=True)
# plt.savefig("football_graph.png")
# plt.show()

pr.settings.verbose = True     # Print info to screen
pr.settings.atom_trace = True  # Print the trace of the atoms

# Load all the files into pyreason
pr.load_graph(g)


@numba.njit
def demanded_player_annotation_fn(annotations, weights):
    """
    Calculate the value of a player based on their attributes.
    """
    # Calculate the value based on the weights
    # print("Annotations: ", annotations)
    # print("Annotations[0]: ", annotations[0])
    num_interested_teams = len(annotations[0])
    print("Interested Teams: ", num_interested_teams)
    if num_interested_teams > 3:
        upper_bound = 1
        lower_bound = 1
    else:
        upper_bound = 0
        lower_bound = 0
    return lower_bound, upper_bound

pr.add_annotation_function(demanded_player_annotation_fn)

# These functions add facts about the players based on how they are drafted and the teams that want them
simulate_draft()
determine_team_interest()

# Rule to check if a player is a free agent
pr.add_rule(pr.Rule('rostered_player(x) <-1 rostered(y, x)', 'rostered_player_rule'))
pr.add_rule(pr.Rule('free_agent(x) <-1 ~rostered(y,x)', 'free_agent_rule'))
pr.add_rule(pr.Rule('make_offer(y,x) <-1 free_agent(x), interested(y,x)', 'make_offer_rule'))
pr.add_rule(pr.Rule('demanded_player(x) : demanded_player_annotation_fn <-1 make_offer(a,x)', 'demanded_player(x)'))
pr.add_rule(pr.Rule('highly_demanded_player(x) <-1 demanded_player(x): [1,1]', 'highly_demanded_player_rule'))

#pr.add_rule(pr.Rule('team_interested_in_player(x, y) <-1 '))

interpretation = pr.reason(timesteps=4)
interpretation_dict = interpretation.get_dict()
# print("Interpretation Dictionary:")
# pprint(interpretation_dict)

# Display the changes in the interpretation for each timestep
print("========================== Rostered Players ==========================")
rostered_player_df = pr.filter_and_sort_nodes(interpretation, ['rostered_player'])
for t, df in enumerate(rostered_player_df):
    print(f'TIMESTEP - {t}')
    print(df)
    print()

print("========================== Free Agents ==========================")
free_agent_df = pr.filter_and_sort_nodes(interpretation, ['free_agent'])
for t, df in enumerate(free_agent_df):
    print(f'TIMESTEP - {t}')
    print(df)
    print()


print("========================== Team offers ==========================")
team_offer_df = pr.filter_and_sort_edges(interpretation, ['make_offer'])
for t, df in enumerate(team_offer_df):
    print(f'TIMESTEP - {t}')
    print(df)
    print()

print("========================== Demanded Player ==========================")
team_offer_df = pr.filter_and_sort_nodes(interpretation, ['demanded_player'])
for t, df in enumerate(team_offer_df):
    print(f'TIMESTEP - {t}')
    print(df)
    print()

print("========================== Hot Commodities ==========================")
hot_commodity_df = pr.filter_and_sort_nodes(interpretation, ['highly_demanded_player'])
for t, df in enumerate(hot_commodity_df):
    print(f'TIMESTEP - {t}')
    print(df)
    for index, row in df.iterrows():
        node_name = row['component']
        player_value = g.nodes[node_name]["player_value"]
        madden_rating = g.nodes[node_name]["madden_rating"]
        expected_salary = g.nodes[node_name]["expected_salary"]
        print(f"Node: {node_name}, Salary: {expected_salary}, Madden Rating: {madden_rating}, Value: {player_value}")


# Iterate over the "component" column in hot_commodity_df and print everything we know about the corresponding node

pr.save_rule_trace(interpretation)
