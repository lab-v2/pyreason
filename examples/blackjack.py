from datetime import timedelta
from pathlib import Path
import random
import sys
import os
import networkx as nx
import numba
import cv2
import torch
from ultralytics import YOLO 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from pyreason.scripts.learning.classification.yolo_classifier import YoloLogicIntegratedTemporalClassifier
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions
from pyreason.scripts.rules.rule import Rule
from pyreason.pyreason import _Settings as Settings, reason, reset_settings, get_rule_trace, add_fact, add_rule, load_graph, save_rule_trace, get_time, Query, add_annotation_function

class Probability_Tensor():
    def __init__(self,
                 label,
                 probability_val,
                 dtype = torch.float32,
                 device=torch.device("cpu")
                ):
        probabilities = torch.tensor([probability_val], dtype=dtype, device=device)
        self.tensor = probabilities
        self.label = label


card_number = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10",
              "J", "Q", "K"]

card_suits = ["h", "d", "c", "s"]

card_names = [
    f"{number}{suit}" for number in card_number for suit in card_suits]


deck_list = []

# draw_random_card()
# PLAYER_CARD_1 = "10s"
# PLAYER_CARD_2 = "8s"
CARD_VALUES = {
    "A": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10
}

# To keep track of player points, we are going to set the 
# lower bound of the holds_card confidence interval to (card_value/10 - assuming ace is 1)
# def add_player_holds_card_fact(card_name, timestep):
#     # Strip away the suit, which is the last character
#     card_value = CARD_VALUES[card_name[:-1]]
#     lower_bound = card_value / 10
#     add_fact(Fact(f"player_holds({card_name}, player_hand): [{lower_bound}, {1}]", "player_holds_fact", start_time=timestep, end_time=timestep))



@numba.njit
def init_hand_annotation_fn(annotations, weights):
    """
    Calculate the value of a player based on their attributes.
    """
    print("Annotations init hand: ", annotations)
    #print("Annotations [0]: ", annotations[0])
    # player_card_value_list = []
    # row = annotations[0]
    # for i in range(len(row)):
    #     # This gets the first item in this numpy object
    #     card_value = row[i].l * 10
    #     print("Card Value: ", card_value)
    #     player_card_value_list.append(card_value)

    # player_hand_point_total = 0
    # for point_val in player_card_value_list:
    #     player_hand_point_total += point_val 
    # print("Total points: ", player_hand_point_total)
    # player_percent_to_busting = min(1, player_hand_point_total / 22)
    row = annotations[0]
    bound_value = 0.0
    place = 0.1  # Start with tenths place
    for i in range(len(row)):
        card_value = row[i].l * 10
        if card_value == 10:
            digit = 0
        else:
            digit = int(card_value)
        bound_value += digit * place
        place *= 0.1  # Move to the next decimal place
    return bound_value, 1

@numba.njit
def hand_percent_to_busting_annotation_fn(annotations, weights):
    """
    Calculate the odds of a player busting based on their hand and the remaining deck.
    """
    print("Annotations perc to busting: ", annotations)
    # current_bust_percent = annotations[0][0].l
    # print("Current Bust Percent: ", current_bust_percent)
    # player_point_total = current_bust_percent * 22
    # print("Player points: ", player_point_total)
    # total_bust_cards = 0
    # row = annotations[1]
    # for i in range(len(row)):
    #     # This gets the first item in this numpy object
    #     card_value = row[i].l * 10
    #     print("Card Value: ", card_value)
    #     if card_value + player_point_total >= 22:
    #         total_bust_cards += 1


    fractional = annotations[0][0].l
    fractional *= 10
    player_card_array = []
    number_player_cards = 0 
    player_point_total = 0
    for val in range(52):
        print("Fractional: ", fractional)
        digit = int(fractional)
        if digit == 0:
            point = 10
        else:
            point = digit
        print("Point: ", point)
        player_point_total += point
        player_card_array.append(point)
        number_player_cards += 1
        fractional -= int(fractional)
        if fractional == 0.0:
            break  # no more digits left
        fractional *= 10
    
    print("Player Point Total: ", player_point_total)
    total_bust_cards = 0
    row = annotations[1]
    for i in range(len(row)):
        # This gets the first item in this numpy object
        card_value = row[i].l * 10
        if card_value in player_card_array:
            print("Found card value in player_card_array: ", card_value)
            player_card_array.remove(card_value)
            continue
        print("Card Value: ", card_value)
        if card_value + player_point_total >= 10:
            total_bust_cards += 1
    print("Total Bust Cards: ", total_bust_cards)
    print("Total cards in deck: ", len(row) - number_player_cards)
    bust_odds = total_bust_cards / (len(row) - number_player_cards)
    print("Odds of busting: ", bust_odds)
    return bust_odds, 1

    
add_annotation_function(init_hand_annotation_fn)
add_annotation_function(hand_percent_to_busting_annotation_fn)

model = YOLO('/Users/coltonpayne/dyuman-pyreason/pyreason/pyreason/train56/weights/best.pt')
training_images_dir = "/Users/coltonpayne/dyuman-pyreason/pyreason/examples/images/cards"


interface_options = ModelInterfaceOptions(
    threshold=0.5,
    set_lower_bound=True,
    set_upper_bound=False,
    snap_value=1.0
)

# def input_function():
#         image = random.choice(list(Path(training_images_dir).glob("*")))
#         print("Path: ", training_images_dir)
#         image = cv2.imread(training_images_dir)
#         return image

# card_drawn_object = YoloLogicIntegratedTemporalClassifier(
#     model,
#     class_names=card_names,
#     identifier="card_drawn_object",
#     interface_options=interface_options,
#     poll_interval=timedelta(seconds=2),
#     input_function=input_function,
#     image_directory=training_images_dir
# )

def add_deck_holds_fact(card_name):
    card_value = CARD_VALUES[card_name[:-1]]
    lower_bound = card_value / 10
    add_fact(Fact(f"deck_holds({card_name}, full_deck): [{lower_bound}, {1}]", "deck_holds_fact"))

# This is the format of fact I will define before any processing - keeps track of the point value 
add_deck_holds_fact("2c")
add_deck_holds_fact("5c")
add_deck_holds_fact("7c")
add_deck_holds_fact("As")

# This is the format of fact that should be returned from the YOLO Classifier.  Each time interval, should return a new fact like this
add_fact(Fact("_2c(card_drawn_obj)", "_2c_drawn_fact"))
add_fact(Fact("_5c(card_drawn_obj)", "_5c_drawn_fact"))

# Init Player Percent to bust and Player odds of busting
add_rule(Rule("player_holds(_2c):[0.2,1] <-0 _2c(card_drawn_obj)", "player_holds_2c_rule"))
add_rule(Rule("player_holds(_5c):[0.5,1] <-0 _5c(card_drawn_obj)", "player_holds_5c_rule"))
add_rule(Rule("player_hand_percent_to_busting(player_hand) : init_hand_annotation_fn <-0 player_holds(card):[0.1,1]", "player_bust_percent_rule"))
add_rule(Rule("player_odds_of_busting(player_hand) : hand_percent_to_busting_annotation_fn <-0 player_hand_percent_to_busting(player_hand):[0,1], deck_holds(card, full_deck):[0.1,1]", "bust_odds_rule"))

# I want to pass the annotation function the cards the player has and the cards the deck has.  I know both of these conditions are met, as they are conditions in other working rules
# However, this annotation function never runs and I can't figure out why.  Decided to encode the cards held in a float instead, but this seems less hacky
#add_rule(Rule("player_odds_of_busting(player_hand) : hand_percent_to_busting_annotation_fn <-0 player_holds(card):[0.1,1], deck_holds(card, full_deck):[0.1,1]", "bust_odds_rule"))

settings = Settings
settings.atom_trace = True
settings.verbose = False

g = nx.DiGraph()
g.add_node("player_hand")
g.add_node("card")
g.add_node("card_drawn_obj")

load_graph(g)
interpretation = reason()
print(f"\n=== Reasoning for Blackjack Iteration: {0} ===")
trace = get_rule_trace(interpretation)
print(f"RULE TRACE: \n\n{trace[0]}\n")
save_rule_trace(interpretation)


#Changes to make
# Remove Dealer Logic and base bust fact around point total of 42
# Add rules for deck hand based on player hand
# Set up YOLO Logic Integrated Classifier and move temporal reasoning to it
# Call Classifier with no game loop