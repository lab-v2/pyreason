How to Create Rules
===================

Introduction
------------

-  Rules are a fundamental part of PyReason. They are used to define the
   relationships between different entities in the graph.
-  In this section we will be looking at creating different types of
   rules.

Creating Rules
--------------

Let us take the examples from the advanced tutorial and create rules for them.
In each of the above rule we have the head of the rule as the a node, i.e. there are no edges

1. A customer x is popular if he is friends with a popular customer after 1 timestep.

.. code-block:: python

    pr.add_rule(pr.Rule('popular(x) <-1 popular(y), Friends(x,y)'))

2. A customer x has cool car if he owns a car y and the car is of type Car_4.

.. code-block:: python

    pr.add_rule(pr.Rule('cool_car(x) <-1 owns_car(x,y),Car_4(y)', 'cool_car_rule'))

In the above example, note that Car_4 is both the node and the attribute of the node.

3. A customer x is a car friend of customer y if they both own the same car and they are not the same person.

.. code-block:: python

    pr.add_rule(pr.Rule("car_friend(x,y) <- owns_car(x,z), owns_car(y,z) , c_id(x) != c_id(y) ", "car_friend_rule"))


Important Tips
---------------

Some points to note about the writing rules

1. The head of the rule is always on the left hand side of the rule.
2. The body of the rule is always on the right hand side of the rule.
3. You can include timestep in the rule by using the `<-timestep` body.
4. You can include multiple bodies in the rule by using the `<-timestep body1, body2, body3`.

.. note::

    5. To compare two nodes, both the nodes should have an attribute in common.
        1. For example , in the below rule , both the customers have an attribute 'c_id' in common which is the customer id.
        2. So, we can compare the customer id of both the customers to check if they are the same person or not.

        .. code-block:: python

            pr.add_rule(pr.Rule("car_friend(x,y) <- owns_car(x,z), owns_car(y,z) , c_id(x) != c_id(y) ", "car_friend_rule"))

6. To compare a particular attribute of a node with another node, you need to use the attribute like in Rule 2 above.
