


import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = "shenzhen_china.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Alley", "Circle", "Center", "Highway", "Terrace", "Way",
           "Close", "Crescent", "Gardens", "Gate", "Heights"]

# UPDATE THIS VARIABLE
mapping = { "St": "Street","St.": "Street","ST": "Street","street":"Street","st": "Street",'Jie':'Street',
            'jie':'Street',
            "Rd": "Road","raod":"Road","road": "Road","Lu":'Road',
            "Ln":"Lane",
            "BLVD": "Boulevard",
            "Acenue": "Avenue", "Ave": "Avenue","avenue": "Avenue", "Av": "Avenue",
            "Hwy": "Highway",
            "Blvd": "Boulevard",
            "Ct": "Court",
            "E": "East","S": "South","W": "West","N": "North",
            "NE": "Northeast","NW": "Northwest","SE": "Southeast","SW": "Southwest",
            "Dadao": "DaDao",
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


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


def update_name(name, mapping):
    words = name.split()
    for i in range(len(words)):
        if words[i] in mapping:
            words[i] = mapping[words[i]]
    name = " ".join(words)
    return name


def test():
    st_types = audit(OSMFILE)
    pprint.pprint(dict(st_types))

    for st_type, ways in st_types.items():
        for name in ways:
            better_name = update_name(name, mapping)
            print (name, "=>", better_name)
            if name == "Fu Shin St.":
                assert better_name == "Fu Shin Street"
            if name == "Shennan BLVD":
                assert better_name == "Shennan Boulevard"


if __name__ == '__main__':
    test()

# Audit postcode

def audit_postcode(filename):
    """
    Args: filename that want to be auditted
    Returns: a set of different postcode
    """
    post_code = set();
    for _, element in ET.iterparse(filename):
        if element.tag == "node" or element.tag == "way":
            for tag in element.iter("tag"):
                if tag.get('k') == 'addr:postcode' and (len(tag.get('v')) != 6 or tag.get('v')[:3] != '518'):
                    post_code.add(tag.get('v'))
    return post_code


postcode_set = audit_postcode(OSMFILE)
pprint.pprint(postcode_set)


def update_postcode(code):
    """
    Args: a postcode to be processed
    Returns: a processed postcode
    """
    if code == '51803031':
        return '518030'
    elif len(code) != 6 or code[:3] != '518':

        return ''


updated_postcode_list = [];
postcode_list = list(postcode_set)
for code in postcode_list:
    updated_postcode_list.append(update_postcode(code))

for i in range(len(postcode_list)):
    print(postcode_list[i], '=>', updated_postcode_list[i])


