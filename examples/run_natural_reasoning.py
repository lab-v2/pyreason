"""
Pipeline:
Natural Language -> Logic -> Natural Language:
User inputs English paragraph, the scipt calls LLM to extract Facts and Rules.
Then calls LLM again to convert the Facts and Rules to PyReason Syntax.
And run the PyReason Inference.
Lastly, calls LLM again to "translate" the inference result in English as outputs.
"""

import ollama
import pyreason as pr
import networkx as nx
import re
import sys
import io

MODEL_NAME = "qwen3:14b"

# Read User Input
print("\nEnter text:")
lines = []
while True:
    line = input()
    if line == "" and lines:
        break
    lines.append(line)
paragraph = " ".join(lines).strip()

print("LLM is generating the conclusion... Please wait ~ 30 seconds")


