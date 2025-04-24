from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import pyreason as pr
import networkx as nx
import torch.nn.functional as F

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
probs = F.softmax(logits, dim=-1)

# --- NEW SECTION: Restrict predictions to a subset of labels ---
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
filtered_probs[0, allowed_indices] = probs[0, allowed_indices]
filtered_probs = filtered_probs / filtered_probs.sum()

# Get top prediction among allowed labels
top_idx = filtered_probs.argmax(-1).item()
top_label = id2label[top_idx].split(",")[0]
top_prob = filtered_probs[0, top_idx].item()

print(f"\nTop prediction (filtered): {top_label} ({top_prob:.4f})")

# Optional: print top N from the filtered subset
top_probs, top_indices = filtered_probs.topk(5)
print("\nTop predictions from allowed subset:")
for prob, idx in zip(top_probs[0], top_indices[0]):
    label = id2label[idx.item()].split(",")[0]
    print(f"{label}: {prob.item():.4f}")


interface_options = pr.ModelInterfaceOptions(
    threshold=0.5,       # Only process probabilities above 0.5
    set_lower_bound=True,  # For high confidence, adjust the lower bound.
    set_upper_bound=False, # Keep the upper bound unchanged.
    snap_value=1.0      # Use 1.0 as the snap value.
)

fish_classifier = pr.LogicIntegratedClassifier(
    model,
    allowed_labels,
    model_name="fish_classifier",
    interface_options=interface_options
)

logits, probabilities, classifier_facts = fish_classifier(image)

print("=== Fish Classifier Output ===")
print("Logits:", logits)
print("Probabilities:", probabilities)
print("\nGenerated Classifier Facts:")
for fact in classifier_facts:
    print(fact)
