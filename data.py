#cleaning phone numbers and street address

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema

OSM_PATH = "sample3.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# regexes 
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
phone_number_re=re.compile(r'^\+1\s\([0-9]{3}\)\s[0-9]{3}\-[0-9]{4}$')
#schema
SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']



# accepted values of street end names used by update_streetname function
expected = ["Street", "Avenue", "Boulevard","Center", "Drive", "Court", "Place","Plaza","Suite", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Way"]

# mapping variable used in update_streetname function
mapping = { 
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "Ct" : "Court",
            "Ct.":"Court",
            "Ctr" :"Center",
            "Ctr." :"Center",
            "Dr": "Drive",
            "Dr." : "Drive",
            "Ln" : "Lane",
            "Ln." : "Lane",
            "Plz" :"Plaza",
            "Plz." :"Plaza",
            "Rd.":"Road",
            "Rd":"Road",
            "Sq" : "Square",
            "Sq." : "Square",
            "St": "Street",
            "St.": "Street",
            "st" : "Street",
            "st." : "Street",
            "Ste" : "Suite",
            "Ste." : "Suite",
            }



def audit_pn_type(number):
    #if(isinstance(number,unicode)):
    number =number #.encode('ascii', 'ignore').decode('ascii')
    m = phone_number_re.search(number)
    if m:        
        return True
    else:
        return False
def check_ext(numeric):
    if len(numeric)>10 and len(numeric)<16:
        return True
    
def get_numeric(s):
    return str(filter(str.isdigit,s))

def update_number(wrong_number):
    if(isinstance(wrong_number,unicode)):
        wrong_number = wrong_number.encode('utf-8')
    numeric=get_numeric(wrong_number)
    
    if len(numeric)==11 and numeric.startswith('1'):
        numeric=numeric[1:]

    if check_ext(numeric):
        newnumber='+1 ({}) {}-{} ext. {}'.format(numeric[0:3], numeric[3:6], numeric[6:10],numeric[10:])
        return newnumber

    elif len(numeric)==10:
        newnumber='+1 ({}) {}-{}'.format(numeric[0:3], numeric[3:6], numeric[6:])
        return newnumber

    else: 
        newnumber="No Phone Number"
        return newnumber


# cleaning function of street names will be called in shape_element function
def update_street_name(name, mapping):
    newname=""
    text=name.split(" ")
    
    for i in range(len(text)):
        if text[i] in mapping:
            #print(text[i])
            text[i]=mapping[text[i]]
            break   
        
    for i in range(len(text)):
        newname=newname+' ' + text[i]
    return newname.strip()

#function to check whether key has colon in it and return the first word before colon as key or 'regular' otherwise       
def is_regular(key):
    if LOWER_COLON.search(key):
        text=key.split(":",1)
        return text[0]
    else:
        return 'regular'
# function to check whether key has colon in it and return the second word after the colon as key or the key otherwise      
def tag_key(key):
    if LOWER_COLON.search(key):
        text=key.split(":",1)
        return text[1]
    else:
        return key
#function to check if key contains problematic characters
def is_probchars(key):
    return PROBLEMCHARS.search(key)
# important function outputs dictionaries of node.attributes, node_tags, way_tags, way.attributes, node_ways.
# the value corresponding to keys street address and phone is cleaned in this section.
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    
    if element.tag == 'node':
        for attribute in element.attrib:
            #print (element.tag)
            if attribute in NODE_FIELDS:
                node_attribs[attribute]=element.attrib[attribute]
            
            #pass
        for child in element:

            # 'tag' elements
            if child.tag == 'tag':

                # parse 'tag' elements
                if PROBLEMCHARS.match(child.attrib["k"]):
                    continue
                
                tag_dict={'id': '',
                    'key': '',
                    'value': '',
                    'type': ''}
                tag_dict["type"] = is_regular(child.attrib["k"])
                tag_dict["key"] = tag_key(child.attrib["k"])
                tag_dict["id"] = element.attrib["id"]

                    # use cleaning function:
                if child.attrib["k"] == 'addr:street':
                    tag_dict["value"] = update_street_name(child.attrib["v"], mapping)
                elif child.attrib["k"]=="phone":
                    if audit_pn_type(child.attrib["v"]):
                        tag_dict["value"] = child.attrib["v"].encode('ascii','ignore')
                    else:
                        tag_dict["value"] = update_number(child.attrib["v"]).encode('ascii','ignore')

                # otherwise:
                else:
                    tag_dict["value"] = child.attrib["v"]
        
                tags.append(tag_dict)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        count=0 
        tags2=[]
        
        for attribute in element.attrib:
            
            if attribute in WAY_FIELDS:
                way_attribs[attribute]=element.attrib[attribute]
            #pass
        for child in element:

            # 'tag' elements
            if child.tag == 'tag':

                # parse 'tag' elements
                if PROBLEMCHARS.match(child.attrib["k"]):
                    continue

                tag_dict={'id': '',
                    'key': '',
                    'value': '',
                    'type': ''}
                tag_dict["type"] = is_regular(child.attrib["k"])
                tag_dict["key"] = tag_key(child.attrib["k"])
                tag_dict["id"] = element.attrib["id"]

                    # use cleaning function:
                if child.attrib["k"] == 'addr:street':
                    tag_dict["value"] = update_street_name(child.attrib["v"], mapping)
                elif child.attrib["k"]=="phone":
                    if audit_pn_type(child.attrib["v"]):
                        tag_dict["value"] = child.attrib["v"].encode('ascii','ignore')
                    else:
                        tag_dict["value"] = update_number(child.attrib["v"]).encode('ascii','ignore')

                    # otherwise:
                else:
                    tag_dict["value"] = child.attrib["v"]
        
                tags2.append(tag_dict)
                       
            elif child.tag=='nd':
                
                way_node_dict={'id': "", 'node_id': "", 'position': ""}
                way_node_dict['id']=element.attrib['id']
                way_node_dict['node_id']=child.attrib['ref']
                way_node_dict['position']=count
                count+=1
                
                way_nodes.append(way_node_dict)
                
            #print (way_node_dict)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags2}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()
        
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
           
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
    
