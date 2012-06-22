from subprocess import check_output, CalledProcessError

from path import path
import tables


def getNodeProper(self, where, *args, **kwargs):
    if isinstance(where, tables.Node):
        node_path = where._v_pathname
        node = self._get_node(node_path, *args, **kwargs)
    else:
        node = self._get_node(where, *args, **kwargs)
    return node


tables.File._get_node = tables.File.getNode
tables.File.getNode = getNodeProper


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
