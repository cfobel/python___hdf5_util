#!/usr/bin/env python

from tables import *
from path import path
import sys
from subprocess import call, check_output
import re

from . import find_command


class HDF5File(object):
    script = find_command('ptrepack')

    def __init__(self, filepath):
        # create the master file
        self.filepath = filepath
        self.master = openFile(str(filepath), 'a')
        self.master_leaves = self.get_leaves()
        self.master_nodes = self.get_nodes()

    def get_leaves(self):
        return set([x._v_pathname for x in self.master.walkNodes()
                if isinstance(x, Leaf)])

    def get_nodes(self):
        return set([x._v_pathname for x in self.master.walkNodes()])

    def append_file(self, filepath):
        fp = openFile(str(filepath), 'r')
        self._append_data(fp)
        self._copy_new_data(fp, filepath)
        fp.close()
        self.master_leaves = self.get_leaves()

    def convert_unnatural_names(self):
        unnatural_name = r'[^0-9A-Za-z_]'
        for node in self.master.walkNodes():
            name = path(node._v_pathname).name
            if not name:
                continue
            natural = re.sub(r'[^0-9A-Za-z_]', '_', name)
            if re.match(r'[0-9]', natural[0]):
                natural = '_' + natural
            if natural != name:        
                self.master.renameNode(node, natural)
        
    def _append_data(self, h5f_input):
        # TODO Add check for id_ and id_ end to keep them up to date.
        # For nodes that already exist in the master, append data
        for atable in [x for x in h5f_input.walkNodes() if isinstance(x, Leaf)]:
            leaf = atable._v_pathname
            if leaf in self.master_leaves:
                mtable = self.master.getNode(leaf)
                if isinstance(atable, Table):
                    for row in atable:
                        mtable.append([[row.fetch_all_fields()]])
                        row = mtable[-1]
                        if 'id_' in atable.colnames:
                            prev_id = mtable[-2]['id_']
                            if 'id_len' in atable.colnames:
                                row['id_'] = prev_id + mtable[-2]['id_len']
                            else:
                                row['id_'] = 1 + prev_id + row['id_']
                            mtable[-1]=[row] # just part of the mystery 
                                             # of the hdf5 library
                else:
                    # must be an Array.
                    for row in atable:
                        mtable.append(row)
    
    def _copy_new_data(self, h5f_input, input_filepath):
        # For nodes that do not already exist in the master, copy the
        # nodes to the master
        nodes = h5f_input.walkNodes()
        for n in nodes:
            name = path(n._v_pathname)
            if name not in self.master_nodes:
                self.master.close()
                cmd = ' '.join(['python', self.script, '%s:%s' % (
                        input_filepath, name), '%s:%s' % (self.filepath, name)])
                call(cmd, shell=True)
                self.master = openFile(self.filepath, 'a')

                # Update list of master nodes, since we added a new node
                self.master_nodes.update([n._v_pathname
                        for n in self.master.walkNodes(name)])

    def __del__(self):
        self.master.close()
