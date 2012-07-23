#!/usr/bin/env python

from tables import *
from path import path
import sys
from subprocess import call, check_output
import re
from .util import find_command
import numpy as np
from path import path


"""
    because of the metaIsDescription metaclass
    the attributes of the Table class have to be specified during it's definition.
    we could only manage this with a string dynamically created.
"""
def T(**kwargs):
    attrs = '\n'.join(['    %s = %s' % (name, repr(_type)) for name, _type in kwargs.items()])
    class_str = '''\
class Table(IsDescription):
%s
    ''' % (attrs)
    exec(class_str)
    return eval('Table')

def python_to_numpy(variable):
    type_map = {int:np.int64, str:np.str, float:np.float, list:np.array}
    if type(variable) in type_map:
        return type_map[type(variable)](variable)
    else:
        return variable

def name(name, make_natural=True):
    if not make_natural:
        return name
    nat_name = re.sub(r'[^0-9a-zA-z]', '_', name)
    if re.match(r'[0-9]', nat_name[0]):
        return '_' + nat_name
    else:
        return nat_name

def hdf5_type(instance):
    hdf5_types = [VLArray, Array, CArray, EArray, IsDescription]
    try:
        types =  [t for t in hdf5_types if issubclass(instance, t)]
    except TypeError:
        return None
    if len(types):
        return types[0]
    else:
        None

def get_create(hdf5, hdf5_type):
    type_map = {VLArray:'VLArray', Array:'Array', EArray:'EArray', 'CArray':CArray, IsDescription:'Table'}
    return getattr(hdf5, 'create' + type_map[hdf5_type])

def _create_subtree(hdf5, parent, node, force_natural=True):
    if isinstance(node[1], tuple):
        new_parent = hdf5.createGroup(parent, name(node[0], force_natural))
        for child in node[1:]:
            _create_subtree(hdf5, new_parent, child)
    else:
        type_ = hdf5_type(node[1])
        if not type_:
            parent._v_attrs[node[0]] = python_to_numpy(node[1])
        else:
            if type_ == IsDescription:
                get_create(hdf5, type_)(parent, name(node[0], force_natural), node[1])
            else:
                get_create(hdf5, type_)(parent, name(node[0], force_natural), node[2])


class HDF5File(object):
    script = find_command('ptrepack')

    @staticmethod
    def create(filepath, tree):
        # create the master file
        HDF5File._createTree(filepath, tree).close()
        return HDF5File(filepath)

    def __init__(self, filepath):
        self.filepath = filepath
        self.master = openFile(filepath, 'a')
        self.master_leaves = self.get_leaves()
        self.master_nodes = self.get_nodes()

    def get_leaf(self, name):
        for leaf in self.master_leaves:
            if path(leaf).namebase == name:
                return self.master.getNode(leaf)
        return None

    @staticmethod
    def _createTree(file_path, structure):
        file_path = path(file_path)
        hdf5 = openFile(file_path, 'w')
        _create_subtree(hdf5, hdf5.root, structure)
        return hdf5

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
                    for i, row in enumerate(atable):
                        mtable.append([[row.fetch_all_fields()]])
                        row = mtable[-1]
                        if 'id_' in atable.colnames:
                            prev_id = mtable[-2]['id_']
                            if i == 0:
                                base = prev_id
                            if 'id_len' in atable.colnames:
                                row['id_'] = prev_id + mtable[-2]['id_len']
                            else:
                                # offset the first index.
                                row['id_'] = base + row['id_'] + 1

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
