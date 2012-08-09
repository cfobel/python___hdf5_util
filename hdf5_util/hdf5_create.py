#/usr/bin/env python
import re
from tables  import *
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


def hdf5_createTree(file_path, structure):
    file_path = path(file_path)
    hdf5 = openFile(file_path, 'w')
    _create_subtree(hdf5, hdf5.root, structure)
    return hdf5


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


def _create_subtree(hdf5, parent, node):
    type_ = hdf5_type(node[1])
    if type_:
        if type_ == IsDescription:
            get_create(hdf5, type_)(parent, node[0], node[1])
        else:
            get_create(hdf5, type_)(parent, node[0], node[2])
    elif isinstance(node[1], str):
        if len(node) > 2:
            new_parent = hdf5.createGroup(parent, node[0], title=node[1])
            for child in node[2:]:
                _create_subtree(hdf5, new_parent, child)
        else:
            parent._v_attrs[node[0]] = node[1]
    elif isinstance(node[1], tuple):
        new_parent = hdf5.createGroup(parent, node[0])
        for child in node[1:]:
            _create_subtree(hdf5, new_parent, child)


def get_node(hdf5, **args):
    return _traverse(hdf5.root, args)

def _traverse(parent, nexts):
    if not nexts:
        return parent
    else:
        return _traverse(getattr(parent, nexts[0]), nexts[1:])

def main(net=path('tseng.net'), algo='BestOverallXover', pop_size=256, tournament_size=32):
    filename = net.namebase + '_' + '.h5'
    net_nat = re.sub(r'[\-\.]', '_', net.namebase)

    h = hdf5_createTree(filename,
            (net_nat, ('_value', np.str(net.namebase)),
                (algo, 'The algorithm',
                    ('pop_size_%d' % pop_size, ('_value', pop_size),
                        ('tournament_size_%d' % tournament_size, ('_value', np.int32(tournament_size)),
                            ('params', 'These Are Parameters',
                                    T(netlist=StringCol(32),
                                    arch=StringCol(32),
                                    pop_size=UInt32Col(),
                                    tournament_size=UInt32Col(),
                                    num_non_improving=UInt32Col(),
                                    stop_threshold=Float32Col())),
                            ('results', T(generation = Int16Col(pos=0),
                                        min_cost = Float32Col(pos=1),
                                        mean_cost = Float32Col(pos=2),
                                        max_cost = Float32Col(pos=3),
                                        num_moves = UInt16Col(pos=4),
                                        num_xovers = UInt16Col(pos=5),
                                        run_time = Float32Col(pos=6),
                                        memory = UInt32Col(pos=7))),
                            ('costs', VLArray, Float32Atom(dflt=-1)),
                            ('grids', VLArray, Int32Atom(dflt=-1))
                        )))))

    tournament = (h, net_nat, algo, 'pop_size_%d' % pop_size, 'tournament_size_%d' % tournament_size)
    return h

if __name__ == "__main__":
    h = main()
    h.close()
