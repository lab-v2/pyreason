import portion
import yaml

from mancalog.scripts.rules.rule import Rule
from mancalog.scripts.components.label import Label


class YAMLParser:

    def __init__(self):
        pass

    def parse_rules(self, path):
        with open(path, 'r') as file:
            rules_yaml = yaml.safe_load(file)

        rules = []
        for _, values in rules_yaml.items():
            target = Label(values['target'])
            target_criteria = []
            for tc in values['target_criteria']:
                target_criteria.append((Label(tc[0]), portion.closed(tc[1], tc[2])))
            
            rule = Rule()

    def parse_facts(self, path):
        with open(path, 'r') as file:
            facts = yaml.safe_load(file)

    def parse_labels(self, path):
        with open(path, 'r') as file:
            labels = yaml.safe_load(file)
    
     