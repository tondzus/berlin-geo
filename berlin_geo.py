#!/usr/bin/env python
# -*- coding: utf-8 -*-

# unicode hack -> http://stackoverflow.com/questions/492483/
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import argparse

import os
import shutil

import csv
import urllib
import codecs
from operator import itemgetter
from subprocess import check_call
from contextlib import contextmanager
from imposm.parser import OSMParser
from lxml import etree


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


PBF_URL = 'http://download.geofabrik.de/europe/germany/' \
          'brandenburg-latest.osm.pbf'
BERLIN_BOUNDS = (52.4510, 13.2691, 52.5801, 13.5321)
CLIPSIZE = itemgetter(1, 3)(BERLIN_BOUNDS), itemgetter(0, 2)(BERLIN_BOUNDS)
LON_LAT_BOX = itemgetter(1, 3, 0, 2)(BERLIN_BOUNDS)
DATASET_PATH = 'node_data.csv'
BERLIN_BACKGROUND_PATH = 'berlin-background.png'


class NodesParser(object):
    def __init__(self):
        self.fp = codecs.open(DATASET_PATH, 'wb', encoding='utf-8')
        self.writer = csv.writer(self.fp)
        self.writer.writerow(['node_id', 'lon', 'lat', 'name', 'street'])
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


def fetch_and_parse_pbf():
    print 'Fetching', PBF_URL
    pbf_file = 'brandenburg-latest.osm.pbf'
    urllib.urlretrieve(PBF_URL, pbf_file)
    np = NodesParser()
    p = OSMParser(concurrency=2, nodes_callback=np.nodes)
    p.parse(pbf_file)
    np.close()
    print 'Dataset', DATASET_PATH, 'with', np.count, 'nodes parsed from OSM xml'


@contextmanager
def inject_db_info(host, user, passwd):
    if all([host, user, passwd]):
        with open('postgresql.xslt') as fp:
            xslt_str = fp.read()
            xslt_str = xslt_str.replace('HOST', host)
            xslt_str = xslt_str.replace('USER', user)
            xslt_str = xslt_str.replace('PASSWD', passwd)
        xslt_xml_root = etree.XML(xslt_str)
        xslt_transform = etree.XSLT(xslt_xml_root)
        mapnik_style_old = etree.parse('mapnik-style.xml')
        mapnik_style_new = xslt_transform(mapnik_style_old)
        with open('tmp.xml', 'w') as fp:
            fp.write(etree.tostring(mapnik_style_new))
    else:
        shutil.copyfile('mapnik-style.xml', 'tmp.xml')

    yield

    os.remove('tmp.xml')


def create_berlin_background(host, user, passwd):
    print 'Generating Berlin background map'
    bbox = map(lambda f: '{:.4f}'.format(f),
               itemgetter(1, 0, 3, 2)(BERLIN_BOUNDS))
    with inject_db_info(host, user, passwd):
        check_call(['nik4.py', '-b'] + bbox +
                   ['-z', '13', 'tmp.xml', BERLIN_BACKGROUND_PATH])


def load_data():
    box = BERLIN_BOUNDS
    data = pd.read_csv(DATASET_PATH)
    lon_filter = (data['lon'] >= box[1]) & (data['lon'] <= box[3])
    lan_filter = (data['lat'] >= box[0]) & (data['lat'] <= box[2])
    return data[lon_filter & lan_filter]


def visualize_data_distribution():
    print 'Loading necessery data'
    berlin = plt.imread(BERLIN_BACKGROUND_PATH)
    shape = map(float, berlin.shape)
    aspect = shape[1] / shape[0]
    data = load_data()

    print 'Ploting density graph over Berlin background'
    dpi = 96
    plt.figure(figsize=(shape[1]/dpi, shape[0]/dpi), dpi=dpi)
    ax = sns.kdeplot(data.lon, data.lat, clip=CLIPSIZE, aspect=aspect)
    ax.imshow(berlin, extent=LON_LAT_BOX, aspect=aspect)
    ax.set_title('"Real" Berlin city center')
    plt.savefig('berlin-center.png', bbox_inches='tight')


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    cmd_help = \
        'prepare - download pbf and parse it\n' \
        'vis - generate background image and plot node density from csv\n'
    parser.add_argument('cmd', choices=['prepare', 'vis'], help=cmd_help)
    parser.add_argument('-H', '--host', help='PostGIS host')
    parser.add_argument('-U', '--user', help='PostGIS user')
    parser.add_argument('-W', '--passwd', help='PostGIS user\'s password')
    parser.add_argument('--skip-bg', action='store_true',
                        help="Don't generate berlin-background.png if present")
    args = parser.parse_args()

    if args.cmd == 'prepare':
        fetch_and_parse_pbf()
    if args.cmd == 'vis':
        if not args.skip_bg or not os.path.exists(BERLIN_BACKGROUND_PATH):
            create_berlin_background(args.host, args.user, args.passwd)
        visualize_data_distribution()


if __name__ == '__main__':
    main()
