import xml.etree.ElementTree as ET
import pprint

def count_tags(filename):
    tags = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag not in tags.keys():
            tags[elem.tag] = 1
        else:
            tags[elem.tag] += 1
    return tags


def test():

    tags = count_tags('shenzhen_china.osm')
    pprint.pprint(tags)




if __name__ == "__main__":
    test()