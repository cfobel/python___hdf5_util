from subprocess import check_output, CalledProcessError

from path import path
import tables

from .append_files import HDF5File, T, HDF5SubTree

def getNodeProper(self, where, *args, **kwargs):
    '''
    original getNode has undefined behavious when passed a node from another file.
    As a work-around, we instead do a lookup based on the path string.
    '''
    if isinstance(where, tables.Node):
        node_path = where._v_pathname
        node = self.__get_node(node_path, *args, **kwargs)
    else:
        node = self.__get_node(where, *args, **kwargs)
    return node

if not tables.File.getNode == getNodeProper:
    tables.File.__get_node = tables.File.getNode
    tables.File.getNode = getNodeProper

"""
def find_command(command_name):
    if command_name.endswith('.py'):
        command_name = command_name[:-len('.py')]

    try:
        script = check_output('which %s' % command_name, shell=True).strip()
        return path(script)
    except CalledProcessError:
        for command_root in ['/usr/lib/python2.7/dist-packages/tables/scripts',
                '/home/cfobel/work/kraken/local/lib/python2.7/site-packages/'\
                        'tables/scripts']:
            script = path(command_root).joinpath('%s.py' % command_name)
            if script.isfile():
                return script
    raise ValueError, 'Script named %s not found' % command_name
"""
