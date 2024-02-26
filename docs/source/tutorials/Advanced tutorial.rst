Running Pyreason with an advanced graph 🚀
==========================================

In this tutorial, we will look at how to run PyReason with a more
complex graph. ## Graph

We can create a graph in two ways: 1. Using Networkx

.. code:: python

   import networkx as nx

   # ================================ CREATE GRAPH====================================
   g = nx.DiGraph()

   customers = ['John', 'Mary', 'Justin', 'Alice', 'Bob']
   cars = [('Toyota Camry', 'Red'), ('Honda Civic', 'Blue'), ('Ford Focus', 'Red'), ('BMW 3 Series', 'Black'),
           ('Tesla Model S', 'Red')]
   pets = ['Dog', 'Cat', 'Rabbit']

   g.add_nodes_from(customers)

   for i, (model, color) in enumerate(cars):
       g.add_node(f"Car_{i}", model=model, color=color)

   g.add_nodes_from(pets)

   friendships = [('Justin', 'Mary'), ('John', 'Mary'), ('John', 'Justin'), ('Alice', 'Bob'), ('Bob', 'John')]
   car_ownerships = [('Mary', 1), ('Justin', 0), ('John', 2), ('Alice', 3), ('Bob', 4), ('Alice', 1), ('Justin', 3),
                     ('Justin', 2)]
   pet_ownerships = [('Mary', 'Cat'), ('Justin', 'Cat'), ('Justin', 'Dog'), ('John', 'Dog'), ('Alice', 'Rabbit'),
                     ('Bob', 'Cat')]

   for f1, f2 in friendships:
       g.add_edge(f1, f2, Friends=1)

   for owner, car_index in car_ownerships:
       g.add_edge(owner, f"Car_{car_index}", owns_car=1)

   for owner, pet in pet_ownerships:
       g.add_edge(owner, pet, owns_pet=1)

.. image:: advanced_graph.png
   :alt: image
    Advanced Graph

Rules
-----

Now we want to add more rules for the graph. The below are the rules we
want to add:
