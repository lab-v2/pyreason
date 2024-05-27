#################################################################################################
#                       Title: Advanced Graph Example                                           #
#                       Description: This example demonstrates how to use PyReason with a more  #
#                       complex graph.                                                          #
#                       Section: tutorials                                                      #
#################################################################################################

#  Imports
from pprint import pprint

import networkx as nx

import pyreason as pr

#  Data about customers - Name,Gender,City,State
customer_details = [
    ('John', 'M', 'New York', 'NY'),
    ('Mary', 'F', 'Los Angeles', 'CA'),
    ('Justin', 'M', 'Chicago', 'IL'),
    ('Alice', 'F', 'Houston', 'TX'),
    ('Bob', 'M', 'Phoenix', 'AZ'),
    ('Eva', 'F', 'San Diego', 'CA'),
    ('Mike', 'M', 'Dallas', 'TX')
]
customer_dict = {i: customer for i, customer in enumerate(customer_details)}

# Data about pets - Species,Class
pet_details = [
    ('Dog', 'Mammal'),
    ('Cat', 'Mammal'),
    ('Rabbit', 'Mammal'),
    ('Parrot', 'Bird'),
    ('Fish', 'Fish')
]
pet_dict = {i: pet for i, pet in enumerate(pet_details)}

# Data about cars - Model,Color

car_details = [
    ('Toyota Camry', 'Red'),
    ('Honda Civic', 'Blue'),
    ('Ford Focus', 'Red'),
    ('BMW 3 Series', 'Black'),
    ('Tesla Model S', 'Red'),
    ('Chevrolet Bolt EV', 'White'),
    ('Ford Mustang', 'Yellow'),
    ('Audi A4', 'Silver'),
    ('Mercedes-Benz C-Class', 'Grey'),
    ('Subaru Outback', 'Green'),
    ('Volkswagen Golf', 'Blue'),
    ('Porsche 911', 'Black')
]

car_dict = {i: car for i, car in enumerate(car_details)}

# Data about travels - Name,Origin City,Origin State,Destination City,Destination State,Duration

travels = [
    ('John', 'Los Angeles', 'CA', 'New York', 'NY', 2),
    ('Alice', 'Houston', 'TX', 'Phoenix', 'AZ', 5),
    ('Eva', 'San Diego', 'CA', 'Dallas', 'TX', 1),
    ('Mike', 'Dallas', 'TX', 'Chicago', 'IL', 3)
]

#  Relationships between customers, pets, and cars

friendships = [('customer_2', 'customer_1'), ('customer_0', 'customer_1'), ('customer_3', 'customer_2'),
               ('customer_3', 'customer_4'), ('customer_4', 'customer_0'), ('customer_5', 'customer_3'),
               ('customer_6', 'customer_0'), ('customer_5', 'customer_6'), ('customer_4', 'customer_6'),
               ('customer_3', 'customer_1')]
car_ownerships = [('customer_1', 'Car_0'), ('customer_2', 'Car_1'), ('customer_0', 'Car_2'), ('customer_3', 'Car_3'),
                  ('customer_4', 'Car_4'), ('customer_3', 'Car_0'), ('customer_2', 'Car_3'), ('customer_5', 'Car_5'),
                  ('customer_6', 'Car_6'), ('customer_0', 'Car_7'), ('customer_1', 'Car_8'), ('customer_4', 'Car_9'),
                  ('customer_3', 'Car_10'), ('customer_2', 'Car_11'), ('customer_5', 'Car_2'), ('customer_6', 'Car_4')]

pet_ownerships = [('customer_1', 'Pet_1'), ('customer_2', 'Pet_1'), ('customer_2', 'Pet_0'), ('customer_0', 'Pet_0'),
                  ('customer_3', 'Pet_2'), ('customer_4', 'Pet_2'), ('customer_5', 'Pet_3'), ('customer_6', 'Pet_4'),
                  ('customer_0', 'Pet_4')]

#  Create a graph
g = nx.DiGraph()

#  Add customers,pets,cars nodes to the graph
for customer_id, details in customer_dict.items():
    attributes = {
        f'c_id-{customer_id}': 1,
        'name': details[0],
        'gender': details[1],
        'city': details[2],
        'state': details[3],
    }
    name = "customer_" + str(customer_id)
    g.add_node(name, **attributes)

for pet_id, details in pet_dict.items():
    dynamic_attribute = f"Pet_{pet_id}"
    attributes = {
        f'pet_id-{pet_id}': 1,
        'species': details[0],
        'class': details[1],
        dynamic_attribute: 1
    }
    name = "Pet_" + str(pet_id)
    g.add_node(name, **attributes)

for car_id, details in car_dict.items():
    dynamic_attribute = f"Car_{car_id}"
    attributes = {
        f'car_id-{car_id}': 1,
        'model': details[0],
        'color': details[1],
        dynamic_attribute: 1
    }
    name = "Car_" + str(car_id)
    g.add_node(name, **attributes)

# Add relationships(edges) between customers, pets, and cars

for f1, f2 in friendships:
    g.add_edge(f1, f2, Friends=1)
for owner, car in car_ownerships:
    g.add_edge(owner, car, owns_car=1, car_color_id=int(car.split('_')[1]))
for owner, pet in pet_ownerships:
    g.add_edge(owner, pet, owns_pet=1)

# Load graph into PyReason
pr.load_graph(g)

pr.settings.verbose = True
pr.settings.atom_trace = True

#  Add rules with only nodes to the graph
pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y)', 'popular_pet_rule'))
pr.add_rule(pr.Rule('cool_car(x) <-1 owns_car(x,y),Car_4(y)', 'cool_car_rule'))
pr.add_rule(pr.Rule('cool_pet(x)<-1 owns_pet(x,y),Pet_2(y)', 'cool_pet_rule'))
pr.add_rule(pr.Rule('trendy(x) <- cool_car(x) , cool_pet(x)', 'trendy_rule'))

#  Add rules with edges to the graph
pr.add_rule(
    pr.Rule("car_friend(x,y) <- owns_car(x,z), owns_car(y,z) , c_id(x) != c_id(y) ", "car_friend_rule"))
pr.add_rule(
    pr.Rule(
        "same_color_car(x, y) <- owns_car(x, c1) , owns_car(y, c2),  car_color_id(x,c1) == car_color_id(y,c2) , c_id(x) != c_id(y)",
        "same_car_color_rule"))

# Add facts to the graph
pr.add_fact(
    pr.Fact(name='popular-fact', component='customer_0', attribute='popular', bound=[1, 1], start_time=0, end_time=5))

# Interpret the graph using pyreason for 6 timesteps
interpretation = pr.reason(timesteps=6)

#  Save the rule trace into two files, one for nodes and one for edges
pr.save_rule_trace(interpretation)

# Get the interpretation dictionary to see the complete interpretation

# interpretations_dict = interpretation.get_interpretation_dict()

#  Get the interpretation for the nodes and edges into dataframes

df_nodes = pr.filter_and_sort_nodes(interpretation, ['trendy', 'cool_car', 'cool_pet', 'popular'])
df_edges = pr.filter_and_sort_edges(interpretation, ['car_friend', 'same_color_car'])

# Print the dataframes
pprint(df_nodes)
pprint(df_edges)
