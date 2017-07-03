#python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-



import unicodecsv as csv
import codecs
import pprint
import re

import xml.etree.cElementTree as ET

# import cerberus
# import schema
# SCHEMA = schema.schema

# validator = cerberus.Validator()

# if validate is True:
#     validate_element(el, validator)

# def validate_element(element, validator, schema=SCHEMA):
#     """Raise ValidationError if element does not match schema"""
#     if validator.validate(element, schema) is not True:
#         field, errors = next(validator.errors.iteritems())
#         message_string = "\nElement of type '{0}' has the following errors:\n{1}"
#         error_string = pprint.pformat(errors)
#         raise Exception(message_string.format(field, error_string))

OSM_PATH = "shenzhen_china.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# Clean data

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

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


def update_street_name(name, mapping = mapping , regex = street_type_re):
    """
    Args: 
        name:  origin street name
        mapping:  street name mapping rule of unexpected street types to appropriate ones
        regex:  regular expressions for extracting the type of name
    Returns: an appropriate street name from origin name
    """
    m = regex.search(name)
    if m:
        st_type = m.group()
        if st_type in mapping:
            name = re.sub(regex, mapping[st_type], name)
    return name


def update_postcode(code):
    """
    Args: a postcode to be processed
    Returns: a processed postcode
    """
    if code == '51803031':
        return '518030'
    elif len(code) != 6 or code[:3] != '518':

        return ''
    else:
        return code




# OSM2CSV


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    id_set = set()

    if element.tag == 'node':
        for Key in NODE_FIELDS:
            node_attribs[Key] = element.get(Key)

        for row in element.iterfind('tag'):
            if PROBLEMCHARS.search(row.get('k')):
                continue
            else:
                node_tag = {}
                node_tag['id'] = node_attribs['id']

                # clean the data
                if row.get('k') == 'addr:postcode':
                    node_tag['value'] = update_postcode(row.get('v'))
                elif row.get('k') == 'addr:street':
                    node_tag['value'] = update_street_name(row.get('v'))
                else:
                    node_tag['value'] = row.get('v')

                if LOWER_COLON.search(row.get('k')):
                    node_tag['key'] = row.get('k').split(':', 1)[1]
                    node_tag['type'] = row.get('k').split(':', 1)[0]
                else:
                    node_tag['key'] = row.get('k')
                    node_tag['type'] = 'regular'
                tags.append(node_tag)


    elif element.tag == 'way':
        for Key in WAY_FIELDS:
            way_attribs[Key] = element.get(Key)

        index = 0
        for row in element.iterfind('nd'):
            way_node = {}
            way_node['id'] = way_attribs['id']
            way_node['node_id'] = int(row.get('ref'))
            way_node['position'] = index
            way_nodes.append(way_node)
            index += 1

        for row in element.iterfind('tag'):
            if PROBLEMCHARS.search(row.get('k')):
                continue
            else:
                way_tag = {}
                way_tag['id'] = way_attribs['id']

                # clean the data
                if row.get('k') == 'addr:postcode':
                    way_tag['value'] = update_postcode(row.get('v'))
                elif row.get('k') == 'addr:street':
                    way_tag['value'] = update_street_name(row.get('v'))
                else:
                    way_tag['value'] = row.get('v')

                if LOWER_COLON.search(row.get('k')):
                    way_tag['key'] = row.get('k').split(':', 1)[1]
                    way_tag['type'] = row.get('k').split(':', 1)[0]
                else:
                    way_tag['type'] = 'regular'
                    way_tag['key'] = row.get('k')
                tags.append(way_tag)

    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


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


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False





# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'wb') as nodes_file, \
            codecs.open(NODE_TAGS_PATH, 'wb') as nodes_tags_file, \
            codecs.open(WAYS_PATH, 'wb') as ways_file, \
            codecs.open(WAY_NODES_PATH, 'wb') as way_nodes_file, \
            codecs.open(WAY_TAGS_PATH, 'wb') as way_tags_file:

        nodes_writer = csv.DictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = csv.DictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = csv.DictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = csv.DictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = csv.DictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
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
    process_map(OSM_PATH, validate=True)
