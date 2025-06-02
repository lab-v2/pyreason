

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
from pyreason.scripts.learning.classification.temporal_classifier import TemporalLogicIntegratedClassifier
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


card_names = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "10",
              "J", "Q", "K"]

card_suits = ["h", "d", "c", "s"]

deck_list = []

model = YOLO('/Users/coltonpayne/dyuman-pyreason/pyreason/pyreason/train56/weights/best.pt')
training_images_dir = "/Users/coltonpayne/dyuman-pyreason/pyreason/examples/images/cards"


def draw_random_card():
    image_path = random.choice(list(Path(training_images_dir).glob("*")))
    print("Path: ", image_path)
    image = cv2.imread(image_path)

    # resized_image = cv2.resize(image, (640, 640))  # Direct resize
    # normalized_image = resized_image / 255.0  # Normalize
    result_predict = model.predict(source = image, imgsz=(640), conf=0.5) #the default image size

    result = result_predict[0]  # Get the first result from the prediction
    box = result.boxes[0]  # Get the first bounding box from the result
    label_id = int(box.cls)
    confidence = float(box.conf)
    label_name = result.names[label_id]  # Get the label name from the names dictionary
    print(f"Predicted label: {label_name}, Confidence: {confidence:.2f}")
    card_prob_object = Probability_Tensor(label_name, confidence)
    return card_prob_object

interface_options = ModelInterfaceOptions(
    threshold=0.5,
    set_lower_bound=True,
    set_upper_bound=False,
    snap_value=1.0
)

card_drawn_object = TemporalLogicIntegratedClassifier(
    model,
    class_names=card_names,
    identifier="card_drawn",
    interface_options=interface_options,
    poll_interval=None,  # No polling, we will draw a card manually
    input_fn=draw_random_card
)

draw_random_card()
PLAYER_CARD_1 = "10s"
PLAYER_CARD_2 = "8s"
DEALER_CARD_1 = "Ks"

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

# To keep track of player and dealer points, we are going to set the 
# lower bound of the holds_card confidence interval to (card_value/10 - assuming ace is 1)
def add_player_holds_card_fact(card_name, timestep):
    # Strip away the suit, which is the last character
    card_value = CARD_VALUES[card_name[:-1]]
    lower_bound = card_value / 10
    add_fact(Fact(f"player_holds({card_name}, player_hand): [{lower_bound}, {1}]", "player_holds_fact", start_time=timestep, end_time=timestep))
    add_not_dealer_holds_card_fact(card_name, timestep)
    add_not_deck_holds_fact(card_name, timestep)

def add_dealer_holds_card_fact(card_name, timestep):
    # Only send the name of the card to the function which is to the left of the underscore
    card_value = CARD_VALUES[card_name[:-1]]
    lower_bound = card_value / 10
    add_fact(Fact(f"dealer_holds({card_name}, dealer_hand): [{lower_bound}, {1}]", "dealer_holds_fact", start_time=timestep, end_time=timestep))
    add_not_player_holds_card_fact(card_name, timestep)
    add_not_deck_holds_fact(card_name, timestep)

def add_deck_holds_fact(card_name, timestep):
    card_value = CARD_VALUES[card_name[:-1]]
    lower_bound = card_value / 10
    add_fact(Fact(f"deck_holds({card_name}, remaining_deck): [{lower_bound}, {1}]", "deck_holds_fact", start_time=timestep, end_time=timestep))
    add_not_dealer_holds_card_fact(card_name, timestep)
    add_not_player_holds_card_fact(card_name, timestep)

def add_not_player_holds_card_fact(card_name, timestep):
    add_fact(Fact(f"~player_holds({card_name}, player_hand)", "not_player_holds_fact", start_time=timestep, end_time=timestep))

def add_not_dealer_holds_card_fact(card_name, timestep):
    add_fact(Fact(f"~dealer_holds({card_name}, dealer_hand)", "not_dealer_holds_fact", start_time=timestep, end_time=timestep))

def add_not_deck_holds_fact(card_name, timestep):
    add_fact(Fact(f"~deck_holds({card_name}, remaining_deck)", "not_deck_holds_fact", start_time=timestep, end_time=timestep))

g = nx.DiGraph()
g.add_node("player_hand")
g.add_node("dealer_hand")
g.add_node("remaining_deck")

for card in card_suits:
    for name in card_names:
        card_name = f"{name}_{card}"
        g.add_node(card_name)
        if card_name != PLAYER_CARD_1 and card_name != PLAYER_CARD_2 and card_name != DEALER_CARD_1:
            deck_list.append(card_name)
        else: 
            print(f"Excluding card {card_name} from deck.")

load_graph(g)

@numba.njit
def init_hand_annotation_fn(annotations, weights):
    """
    Calculate the value of a player based on their attributes.
    """
    #print("Annotations: ", annotations)
    #print("Annotations [0]: ", annotations[0])
    player_card_value_list = []
    row = annotations[0]
    for i in range(len(row)):
        # This gets the first item in this numpy object
        card_value = row[i].l * 10
        #print("Card Value: ", card_value)
        player_card_value_list.append(card_value)

    # Account for the fact that an ace can be 1 or 11 
    # We count them last and value them at 11 if the 
    player_card_value_list.sort(reverse=True)
    ace_count = player_card_value_list.count(1)
    player_hand_point_total = 0
    for point_val in player_card_value_list:
        # If you have a nine and two aces, you can only count one ace as 11
        if point_val == 1 and player_hand_point_total <= 10 - ace_count + 1:
            player_hand_point_total += 11
        else:
            player_hand_point_total += point_val
        ace_count -= 1
    
    #print("Total points: ", player_hand_point_total)
    player_bust_odds = min(1, player_hand_point_total / 22)
    return player_bust_odds, 1

@numba.njit
def hand_percent_to_busting_annotation_fn(annotations, weights):
    """
    Calculate the odds of a player busting based on their hand and the remaining deck.
    """
    #print("Annotations: ", annotations)
    current_bust_percent = annotations[0][0].l
    #print("Current Bust Percent: ", current_bust_percent)
    player_point_total = current_bust_percent * 22
    #print("Player points: ", player_point_total)
    total_bust_cards = 0
    row = annotations[1]
    for i in range(len(row)):
        # This gets the first item in this numpy object
        card_value = row[i].l * 10
        if card_value + player_point_total >= 22:
            total_bust_cards += 1

    # print("Total Bust Cards: ", total_bust_cards)
    # print("Total cards in deck: ", len(row))
    bust_odds = total_bust_cards / len(row)
    print("Odds of busting: ", bust_odds)

    return bust_odds, 1

    
add_annotation_function(init_hand_annotation_fn)
add_annotation_function(hand_percent_to_busting_annotation_fn)

add_player_holds_card_fact(PLAYER_CARD_1, 0)
add_player_holds_card_fact(PLAYER_CARD_2, 0)
add_dealer_holds_card_fact(DEALER_CARD_1, 0)
add_deck_holds_fact("Ac", 0)
add_deck_holds_fact("5c", 0)


# Init Player Percent to bust and Player odds of busting
add_rule(Rule("player_hand_percent_to_busting(player_hand) : init_hand_annotation_fn <-0 player_holds(card, player_hand):[0.1,1]", "player_bust_percent_rule"))
add_rule(Rule("player_odds_of_busting(player_hand) : hand_percent_to_busting_annotation_fn <-0 player_hand_percent_to_busting(player_hand):[0,1], deck_holds(card, remaining_deck):[0.1,1]", "bust_odds_rule"))

max_iters = 2
for blackjack_iter in range(max_iters):
    settings = Settings
    settings.atom_trace = True
    settings.verbose = False
    # if blackjack_iter == 1:
        # print("Drawing Random Card...")
        # #drawn_card = draw_random_card()
        # add_player_holds_card_fact("2h")
    again = False if blackjack_iter == 0 else True
    interpretation = reason(timesteps=2, again=again, restart=False)
    print(f"\n=== Reasoning for Blackjack Iteration: {blackjack_iter} ===")
    trace = get_rule_trace(interpretation)
    print(f"RULE TRACE: \n\n{trace[0]}\n")
    save_rule_trace(interpretation)

