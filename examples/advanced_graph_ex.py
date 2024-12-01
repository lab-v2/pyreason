from pprint import pprint
import networkx as nx
import pyreason as pr

# Customer Data
customers = ['John', 'Mary', 'Justin', 'Alice', 'Bob', 'Eva', 'Mike']
customer_details = [
    ('John', 'M', 'New York', 'NY'),
    ('Mary', 'F', 'Los Angeles', 'CA'),
    ('Justin', 'M', 'Chicago', 'IL'),
    ('Alice', 'F', 'Houston', 'TX'),
    ('Bob', 'M', 'Phoenix', 'AZ'),
    ('Eva', 'F', 'San Diego', 'CA'),
    ('Mike', 'M', 'Dallas', 'TX')
]

# Creating a dictionary of customers with their details
customer_dict = {i: customer for i, customer in enumerate(customer_details)}

# Pet Data
pet_details = [
    ('Dog', 'Mammal'),
    ('Cat', 'Mammal'),
    ('Rabbit', 'Mammal'),
    ('Parrot', 'Bird'),
    ('Fish', 'Fish')
]

# Creating a dictionary of pets with their details
pet_dict = {i: pet for i, pet in enumerate(pet_details)}

# Car Data
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

# Creating a dictionary of cars with their details
car_dict = {i: car for i, car in enumerate(car_details)}

# Travel Data (customer movements between cities)
travels = [
    ('John', 'Los Angeles', 'CA', 'New York', 'NY', 2),
    ('Alice', 'Houston', 'TX', 'Phoenix', 'AZ', 5),
    ('Eva', 'San Diego', 'CA', 'Dallas', 'TX', 1),
    ('Mike', 'Dallas', 'TX', 'Chicago', 'IL', 3)
]

# Friendships (who is friends with whom)
friendships = [('customer_2', 'customer_1'), ('customer_0', 'customer_1'), ('customer_0', 'customer_2'),
               ('customer_3', 'customer_4'), ('customer_4', 'customer_0'), ('customer_5', 'customer_3'),
               ('customer_6', 'customer_0'), ('customer_5', 'customer_6'), ('customer_4', 'customer_5'),
               ('customer_3', 'customer_1')]

# Car Ownerships (who owns which car)
car_ownerships = [('customer_1', 'Car_0'), ('customer_2', 'Car_1'), ('customer_0', 'Car_2'), ('customer_3', 'Car_3'),
                  ('customer_4', 'Car_4'), ('customer_3', 'Car_0'), ('customer_2', 'Car_3'), ('customer_5', 'Car_5'),
                  ('customer_6', 'Car_6'), ('customer_0', 'Car_7'), ('customer_1', 'Car_8'), ('customer_4', 'Car_9'),
                  ('customer_3', 'Car_10'), ('customer_2', 'Car_11'), ('customer_5', 'Car_2'), ('customer_6', 'Car_4')]

# Pet Ownerships (who owns which pet)
pet_ownerships = [('customer_1', 'Pet_1'), ('customer_2', 'Pet_1'), ('customer_2', 'Pet_0'), ('customer_0', 'Pet_0'),
                  ('customer_3', 'Pet_2'), ('customer_4', 'Pet_2'), ('customer_5', 'Pet_3'), ('customer_6', 'Pet_4'),
                  ('customer_0', 'Pet_4')]

# Create a directed graph
g = nx.DiGraph()

# Add nodes for customers
for customer_id, details in customer_dict.items():
    attributes = {
        'c_id': customer_id,
        'name': details[0],
        'gender': details[1],
        'city': details[2],
        'state': details[3],
    }
    name = "customer_" + str(customer_id)
    g.add_node(name, **attributes)

# Add nodes for pets
for pet_id, details in pet_dict.items():
    dynamic_attribute = f"Pet_{pet_id}"
    attributes = {
        'pet_id': pet_id,
        'species': details[0],
        'class': details[1],
        dynamic_attribute: 1
    }
    name = "Pet_" + str(pet_id)
    g.add_node(name, **attributes)

# Add nodes for cars
for car_id, details in car_dict.items():
    dynamic_attribute = f"Car_{car_id}"
    attributes = {
        'car_id': car_id,
        'model': details[0],
        'color': details[1],
        dynamic_attribute: 1
    }
    name = "Car_" + str(car_id)
    g.add_node(name, **attributes)

# Add edges for relationships
for f1, f2 in friendships:
    g.add_edge(f1, f2, Friends=1)
for owner, car in car_ownerships:
    g.add_edge(owner, car, owns_car=1, car_color_id=int(car.split('_')[1]))
for owner, pet in pet_ownerships:
    g.add_edge(owner, pet, owns_pet=1)

# Load the graph into PyReason
pr.load_graph(g)

# Set PyReason settings
pr.settings.verbose = True
pr.settings.atom_trace = True

# Define logical rules
pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y)', 'popular_pet_rule'))
pr.add_rule(pr.Rule('cool_car(x) <-1 owns_car(x,y),Car_4(y)', 'cool_car_rule'))
pr.add_rule(pr.Rule('cool_pet(x)<-1 owns_pet(x,y),Pet_2(y)', 'cool_pet_rule'))
pr.add_rule(pr.Rule('trendy(x) <- cool_car(x) , cool_pet(x)', 'trendy_rule'))

pr.add_rule(
    pr.Rule("car_friend(x,y) <- owns_car(x,z), owns_car(y,z)", "car_friend_rule"))
pr.add_rule(
    pr.Rule("same_color_car(x, y) <- owns_car(x, c1) , owns_car(y, c2)","same_car_color_rule"))


# Add a fact about 'customer_0' being popular
pr.add_fact(pr.Fact('popular-fact', 'popular(customer_0)', 0, 5))

# Perform reasoning over 10 timesteps
interpretation = pr.reason(timesteps=5)

# Get the interpretation and display it
interpretations_dict = interpretation.get_dict()
pprint(interpretations_dict)

# Filter and sort nodes based on specific attributes
df1 = pr.filter_and_sort_nodes(interpretation, ['trendy', 'cool_car', 'cool_pet', 'popular'])

# Filter and sort edges based on specific relationships
df2 = pr.filter_and_sort_edges(interpretation, ['car_friend', 'same_color_car'])

#pr.save_rule_trace(interpretation)

# Display filtered node and edge data
print(df1)
print(df2)
