from datetime import timedelta
from pathlib import Path
import random
import shutil
import sys
import os
from time import sleep
import networkx as nx
import numba
import cv2
import torch
from ultralytics import YOLO 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from pyreason.scripts.learning.classification.yolo_classifier import YoloLogicIntegratedTemporalClassifier
from pyreason.scripts.learning.classification.temporal_classifier import TemporalLogicIntegratedClassifier
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions
from pyreason.scripts.rules.rule import Rule
from pyreason.pyreason import _Settings as Settings, reason, reset_settings, get_rule_trace, add_fact, add_rule, load_graph, save_rule_trace, get_time, Query, add_annotation_function, get_logic_program


MODEL = YOLO('/Users/coltonpayne/dyuman-pyreason/pyreason/pyreason/train56/weights/best.pt')
TRAINING_IMAGES_DIR = "/Users/coltonpayne/dyuman-pyreason/pyreason/examples/images/cards"

CARD_NUMBERS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10",
              "J", "Q", "K"]

CARD_SUITS = ["h", "d", "c", "s"]

CARD_NAMES = [
    f"{number}{suit}" for number in CARD_NUMBERS for suit in CARD_SUITS]

MAX_POINTS = 42

CARD_VALUES = {
    "A": 3,
    "2": 6,
    "3": 6,
    "4": 6,
    "5": 6,
    "6": 6,
    "7": 6,
    "8": 6,
    "9": 6,
    "10": 6,
    "J": 9,
    "Q": 9,
    "K": 9
}

# Move all images back to the training directory after a run
def reset_used_images():
    training_dir = Path(TRAINING_IMAGES_DIR)
    used_dir = training_dir / "used"

    if not used_dir.exists():
        print("No 'used' folder found. Nothing to reset.")
        return

    for file in used_dir.iterdir():
        if file.is_file():
            shutil.move(str(file), str(training_dir / file.name))

@numba.njit
def init_hand_annotation_fn(annotations, weights):
    """
    Given all the cards in a players hand, return a decimal representation of the hand.
    Each point value of a card is a digit in the decimal representation.
    """
    row = annotations[0]
    digits = 0
    num_digits = 0

    for i in range(len(row)):
        card_value = int(row[i].l * 10)
        digits = digits * 10 + card_value
        num_digits += 1

    bound_value = digits / (10 ** num_digits)
    print("Points in player hand: ", bound_value)
    return bound_value, 1


@numba.njit
def hand_percent_to_losing_annotation_fn(annotations, weights):
    """
    Calculate the odds of a player losing based on their hand and the remaining deck,
    Given a decimal representation of the players hand and knowlege of the cards in the full deck
    """
    fractional = annotations[0][0].l
    # First, we need to see how many cards are in the player's hand
    num_player_cards = 52
    initial_num_player_cards = 0
    scale = 1
    for d in range(1, 52 + 1):
        scale *= 10
        scaled = fractional * scale
        int_check = abs(scaled - int(scaled))
        if int_check < 1e-8:  # close enough to an int
            initial_num_player_cards = d
            break
    num_player_cards = initial_num_player_cards
    fractional *= 10
    player_card_array = []
    player_point_total = 0
    # Now, we need to get the total number of points in the players hand.
    # We also make an array of the point total the player has so we can remove equivalent cards from the game deck
    for val in range(num_player_cards):
        digit = int(fractional)
        player_point_total += digit
        player_card_array.append(digit)
        fractional -= int(fractional)
        # Add back a small floating point amount to avoid floating point precision issues
        fractional += 1e-8
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
            player_card_array.remove(card_value)
            continue
        #print("Card Value: ", card_value)
        if card_value + player_point_total > MAX_POINTS:
            total_bust_cards += 1
    bust_odds = total_bust_cards / (len(row) - num_player_cards)
    print("Odds of losing on next card draw: ", bust_odds)
    if bust_odds >= 1:
        print("Every remaining card will put you over the point total.  The game is over!")
        print("Player Final Score: ", player_point_total)
        bust_odds = 1

    return bust_odds, 1

    
add_annotation_function(init_hand_annotation_fn)
add_annotation_function(hand_percent_to_losing_annotation_fn)

# Use these helper functions to make facts and rules for all the cards in the deck.
def add_deck_holds_fact(card_name):
    card_value = CARD_VALUES[card_name[:-1]]
    lower_bound = card_value / 10
    add_fact(Fact(f"deck_holds({card_name}, full_deck): [{lower_bound}, {1}]", "deck_holds_fact"))

def add_player_holds_rule(card_name):
    card_value = CARD_VALUES[card_name[:-1]]
    lower_bound = card_value / 10
    add_rule(Rule(f"player_holds(_{card_name}): [{lower_bound}, 1] <-0 _{card_name}(card_drawn_obj)", f"player_holds_{card_name}_rule"))


# This is the format of fact that should be returned from the YOLO Classifier.  Each time interval, should return a new fact like this.  
# We start the game with the player holding one card.
print("Initializing game...")

# Initialize the deck and player holds rules for each card in the deck.
for card in CARD_NAMES:
    add_deck_holds_fact(card)
    add_player_holds_rule(card)

add_fact(Fact("_2c(card_drawn_obj)", "_2c_drawn_fact"))
add_rule(Rule("player_hand_percent_to_losing(player_hand) : init_hand_annotation_fn <-0 player_holds(card):[0.1,1]", "player_bust_percent_rule"))
add_rule(Rule("player_odds_of_losing(player_hand) : hand_percent_to_losing_annotation_fn <-0 player_hand_percent_to_losing(player_hand):[0,1], deck_holds(card, full_deck):[0.1,1]", "bust_odds_rule"))

settings = Settings
settings.atom_trace = True
settings.verbose = False

# Input function for temporal classifier
# For yolo models, the input function should return an image.
def input_function():
        random.seed()
        available_images = [p for p in Path(TRAINING_IMAGES_DIR).glob("*") if p.is_file()]
        if not available_images:
            print("No images left.")
            return None
        image_path = random.choice(available_images)
        print("Path:", image_path)
        image = cv2.imread(str(image_path))
        # Move image to a "used" folder so it doesn't draw the same card again
        shutil.move(str(image_path), str(Path(TRAINING_IMAGES_DIR) / "used" / image_path.name))
        return image

interface_options = ModelInterfaceOptions(
    threshold=0.5,
    set_lower_bound=True,
    set_upper_bound=False,
    snap_value=1.0
)

card_drawn_object = YoloLogicIntegratedTemporalClassifier(
    MODEL,
    class_names=CARD_NAMES,
    identifier="card_drawn_obj",
    interface_options=interface_options,
    poll_interval=timedelta(seconds=5),
    input_fn=input_function,
)

interpretation = reason()
logic_program = get_logic_program()
interp = logic_program.interp
for i in range(200):
    print("Quering game end condition...")
    result = interp.query(Query("player_odds_of_losing(player_hand)"))
    if result:
        print("Player can not draw any more cards without going over the point total. Ending game.")
        break
    sleep(1)

# Save the rule trace and move all images from the 'used' directory.
save_rule_trace(interpretation)
reset_used_images()