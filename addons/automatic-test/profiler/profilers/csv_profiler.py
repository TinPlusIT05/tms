# -*- encoding: utf-8 -*-

import csv
import os
import time

import logging
logger = logging.getLogger('tracker')


class CSVProfiler(object):

    def __init__(self, file_path, columns, delimiter=',', quotechar='"'):
        self.file_path = file_path
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.columns = columns


    def init(self):
        """
        Write a CSV column headers
        """
        if len(self.columns) <= 0:
            raise Exception('CSVHandler need at least 1 column')

        self.writefile(self.columns, mode='w+')

    def write(self, *args):
        """
        Write a data row in CSV
        """
        if len(args) != len(self.columns):
            raise TypeError('csv file is composed of %s columns (%s given)' % (len(self.columns), len(args)))

        self.writefile(args)

    def writefile(self, data, mode='a+'):
        """
        Write a row in CSV
        """
        with open(self.file_path, mode) as csv_file:
            writer = csv.writer(csv_file, delimiter=self.delimiter, quotechar=self.quotechar)
            writer.writerow(data)

