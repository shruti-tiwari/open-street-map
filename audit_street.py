#Code to audit street names. The output contains a 
#dictionary with unique entries of abbreviated names as keys and a list of full street names 
#as values.

# this function inputs street name and
from collections import defaultdict
import xml.etree.cElementTree as ET
import re

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard","Center", "Drive", "Court", "Place","Plaza","Suite", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Way"]

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

# outputs boolean 
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

if __name__ == '__main__':
    
    audit('sample3.osm')
