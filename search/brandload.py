import yaml
from pprint import pprint
with open('brands.yml', 'r') as f:
    doc = yaml.load(f)
pprint(doc)
