# import the logicIntegratedClassifier class

import torch
import torch.nn as nn
import networkx as nx
import numpy as np
import random
import sys
import os
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch.nn.functional as F
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pyreason.scripts.learning.classification.classifier import LogicIntegratedClassifier
from pyreason.scripts.facts.fact import Fact
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions
from pyreason.scripts.rules.rule import Rule
from pyreason.pyreason import _Settings as Settings, reason, reset_settings, get_rule_trace, add_fact, add_rule, load_graph


# Step 1: Load a pre-trained model and image processor from Hugging Face
model_name = "google/vit-base-patch16-224"  # Vision Transformer model
processor = AutoImageProcessor.from_pretrained(model_name)
model = AutoModelForImageClassification.from_pretrained(model_name)

# Step 2: Load and preprocess an image
image_path = "/Users/coltonpayne/pyreason/examples/image_classifier_two/goldfish.jpeg"
image = Image.open(image_path)

inputs = processor(images=image, return_tensors="pt")

# Step 3: Run the image through the model
with torch.no_grad():
    outputs = model(**inputs)

# Step 4: Get the logits and apply softmax
logits = outputs.logits
probs = F.softmax(logits, dim=-1).squeeze()

# Define your allowed labels
allowed_labels = ['goldfish', 'tiger shark', 'hammerhead', 'great white shark', 'tench']

# Get the index-to-label mapping from the model config
id2label = model.config.id2label

# Get the indices of the allowed labels
# Get the indices of the allowed labels, stripping everything after the comma
allowed_indices = [
    i for i, label in id2label.items()
    if label.split(",")[0].strip().lower() in [name.lower() for name in allowed_labels]
]


# Filter and re-normalize probabilities
filtered_probs = torch.zeros_like(probs)
filtered_probs[allowed_indices] = probs[allowed_indices]
filtered_probs = filtered_probs / filtered_probs.sum()

# Get top prediction among allowed labels
top_idx = filtered_probs.argmax(-1).item()
top_label = id2label[top_idx].split(",")[0]
top_prob = filtered_probs[top_idx].item()

print(f"\nTop prediction (filtered): {top_label} ({top_prob:.4f})")

# Optional: print top N from the filtered subsetc
top_probs, top_indices = filtered_probs.topk(5)
print("\nTop predictions from allowed subset:")
for prob, idx in zip(top_probs, top_indices):
    label = id2label[idx.item()].split(",")[0]
    print(f"{label}: {prob.item():.4f}")


interface_options = ModelInterfaceOptions(
    threshold=0.5,       # Only process probabilities above 0.5
    set_lower_bound=True,  # For high confidence, adjust the lower bound.
    set_upper_bound=False, # Keep the upper bound unchanged.
    snap_value=1.0      # Use 1.0 as the snap value.
)

fish_classifier = LogicIntegratedClassifier(
    model,
    allowed_labels,
    identifier="fish_classifier",
    interface_options=interface_options
)
print("Top Probs: ", top_probs)
#logits, probabilities, classifier_facts = fish_classifier(inputs, output=logits, probabilities=top_probs)
#logits, probabilities, classifier_facts = fish_classifier(inputs)
logits, probabilities, classifier_facts = fish_classifier(**inputs)

print("=== Fish Classifier Output ===")
print("Probabilities:", probabilities)
print("\nGenerated Classifier Facts:")
for fact in classifier_facts:
    print(fact)
