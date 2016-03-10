#!/usr/bin/env python
# -*- coding: utf-8 -*-

# unicode hack -> http://stackoverflow.com/questions/492483/
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import argparse

import os
import csv
import urllib
import codecs
from operator import itemgetter
from subprocess import check_call
#import overpass
from imposm.parser import OSMParser


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


PBF_URL = 'http://download.geofabrik.de/europe/germany/' \
          'brandenburg-latest.osm.pbf'
BERLIN_BOUNDS = (52.4510, 13.2691, 52.5801, 13.5321)
CLIPSIZE = itemgetter(1, 3)(BERLIN_BOUNDS), itemgetter(0, 2)(BERLIN_BOUNDS)
LON_LAT_BOX = itemgetter(1, 3, 0, 2)(BERLIN_BOUNDS)
LOCAL_CACHE_PATH = 'brandenburg-latest.osm'
DATASET_PATH = 'restaurants.csv'


class NodesParser(object):
    def __init__(self):
        self.fp = codecs.open(DATASET_PATH, 'wb', encoding='utf-8')
        self.writer = csv.writer(self.fp)
        self.writer.writerow(['node_id', 'long', 'lat', 'name', 'street'])
        self.count = 0

    def nodes(self, nodes):
        for nid, tags, pos in nodes:
            if not 'amenity' in tags or tags['amenity'] != 'restaurant':
                continue
            row = [nid, pos[0], pos[1],
                   tags.get('name', ''), tags.get('addr:street', '')]
            self.writer.writerow(row)
            self.count += 1

    def close(self):
        self.fp.close()


#def fetch_data_overpass():
#    api = overpass.API()
#    print 'Fetching data from', api.endpoint
#    berlin_box = '{:.4f}, {:.4f}, {:.4f}, {:.4f}'.format(*BERLIN_BOUNDS)
#    query = 'node({});out;'.format(berlin_box)
#    with codecs.open(LOCAL_CACHE_PATH, 'w', encoding='utf-8') as fp:
#        response = api.Get(query)
#        fp.write(response)
#    print 'Data stored to', LOCAL_CACHE_PATH


def fetch_and_convert_pbf():
    pbf_file = 'brandenburg-latest.osm.pbf'

    if os.path.exists(LOCAL_CACHE_PATH):
        print LOCAL_CACHE_PATH, 'already exist, won\'t fetch/convert again'
        return

    if not os.path.exists(pbf_file):
        print 'Fetching', PBF_URL
        urllib.urlretrieve(PBF_URL, pbf_file)
    else:
        print 'Warning: Will use existing', pbf_file

    print 'Converting', pbf_file, 'to osm file format'
    check_call(['osmconvert', pbf_file, '--drop-author',
                '-o=' + LOCAL_CACHE_PATH])


def parse_data():
    np = NodesParser()
    p = OSMParser(concurrency=2, nodes_callback=np.nodes)
    p.parse(LOCAL_CACHE_PATH)
    np.close()
    print 'Dataset', DATASET_PATH, 'with', np.count, 'nodes parsed from OSM xml'


def create_berlin_background():
    path = 'berlin-background.png'
    bbox = map(lambda f: '{:.4f}'.format(f),
               itemgetter(1, 0, 3, 2)(BERLIN_BOUNDS))
    check_call(['nik4.py', '-b'] + bbox +
               ['-z', '12', 'mapnik-style.xml', path])
    return path


def visualize_data_distribution():
    print 'Generating Berlin background map'
    berlin = plt.imread(create_berlin_background())
    aspect = float(berlin.shape[0]) / berlin.shape[1]

    print 'Filtering data to bounding box selection'
    box = BERLIN_BOUNDS
    data = pd.read_csv(DATASET_PATH)
    lon_filter = (data['long'] >= box[1]) & (data['long'] <= box[3])
    lan_filter = (data['lat'] >= box[0]) & (data['lat'] <= box[2])
    data = data[lon_filter & lan_filter]

    print 'Ploting density graph over Berlin background'
    plt.figure(figsize=(30, 30*aspect))
    ax = sns.kdeplot(data['long'], data['lat'], clip=CLIPSIZE, aspect=1/aspect)
    ax.imshow(berlin, extent=LON_LAT_BOX, aspect=aspect)
    plt.savefig('berlin-center.png')


def main():
    parser = argparse.ArgumentParser()
    fetch_help = 'Fetch data from OSM. If not set {} must be present'.format(
        LOCAL_CACHE_PATH)
    parser.add_argument('--fetch', action='store_true', help=fetch_help)
    parser.add_argument('--parse', action='store_true',
                        help='Parse downloaded OSM data')
    parser.add_argument('--vis', action='store_true',
                        help='Visualize Berlin\'s centers')
    parser.add_argument('--all', action='store_true',
                        help='Perform all three steps: fetch, parse and vis')
    args = parser.parse_args()

    if args.fetch or args.all:
        fetch_and_convert_pbf()
    if args.parse or args.all:
        parse_data()
    if args.vis or args.all:
        visualize_data_distribution()


if __name__ == '__main__':
    main()

