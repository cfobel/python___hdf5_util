#!/usr/bin/env python


#TODO Add support for arrays and positions
# Add attributes to dot file
# get rid of variables?

class Group(object):
    def __init__(self, *args):
        if len(args) < 2:
            raise ValueError('Group Must Have children and title')
        self.name = args[0]
        self.children = list()
        child_start = 1
        if isinstance(args[1], str):
            self.description = args[1]
            child_start = 2
            if len(args) == 2:
                raise ValueError('Group Must Have children')
        else:
            self.description = ""
        for child in args[child_start:]:
            self.children.append(child)
        self.attributes = dict()

    def __repr__(self):
        return "Group(" + self.name + ")"

    def __str__(self):
        return self.name

    def dot(self):
        dot_text = '"%s";\n' % self.name
        rank = "rank = same;"
        for child in self.children:
            rank += '"%s";' % child.name
            dot_text += '"%s"->"%s";\n' % (self.name, child.name)
        rank += '\n'
        dot_text += rank
        return dot_text

class Array(object):
    pass


class Table(object):
    "Needs a way to specify position"
    def __init__(self, *args, **kwargs):
        self.colnames = list()
        self.types = list()
        self.descriptions = list()
        self.name = args[0]
        if len(args) > 1:
            self.description = args[1]
        else:
            self.description = ""
        self.kwargs = kwargs

        for name, desc in kwargs.items():
            if isinstance(desc, tuple):
                self.descriptions.append(desc[1])
                self.types.append(desc[0])
            else:
                self.descriptions.append("")
                self.types.append(desc)
            self.colnames.append(name)

    def _repr_item(self, i):
        return self.colnames[i] + '=(' +\
                self.types[i].__name__ + ', ' +\
                repr(self.descriptions[i]) + ')'

    def _str_item(self, i):
        return self.colnames[i] + ":'" +\
                self.descriptions[i] + "'"


    def dot(self):
        fields = '{' + '|'.join([col  for col in self.colnames]) + '}'
        dot_text = """"%s" [shape=record, label="%s|%s"];\n""" % (self.name, self.name, fields)
        return dot_text

    def __repr__(self):
        return "Table(" + ', '.join([repr(self.name), repr(self.description)] +
                [self._repr_item(i) for i in range(
                    len(self.types))]) + ')'

    def __str__(self):
        return self.name + ': ' + self.description + '\n\t' +\
                '\n\t'.join([self._str_item(i) for i in range(
                len(self.types))])


class Variable(object):
    def __init__(self, desc="", **kwargs):
        self.key, self.type = kwargs.items()[0]
        self.value = None
        self.description = desc

    def __str__(self):
        return self.key + '=' + str(self.value)

    def __repr__(self):
        return 'Variable(' + self.key + '=' +\
                self.type.__name__ + ')'

    def defined(self):
        return self.value is not None

    def set(self, value):
        self.value = value


class Attribute(object):
    def __init__(self, *args, **kwargs):
        if args:
            self.key, self.value = args
        else:
            self.key, self.value = kwargs.items()[0]

    def __repr__(self):
        return 'Attribute(' + self.key + '=' +\
                repr(self.value) + ')'

    def __str__(self):
        return self.key + '=' + str(self.value)


class Tree(object):
    def __init__(self, *args):
        self.variables = list()
        self.tables = list()
        self.arrays = list()
        self.tree = args
        self.name = args[0]
        child_start = 1
        self.description = ""
        if len(args) > 1:
            if isinstance(args[1], str):
                child_start = 2
                self.description = args[1]

        self.root = Group('root', self.name, *args[child_start:])
        children = list()
        for subtree in self.root.children:
            children.append(self._create_subtree(self.root, subtree))
        self.root.children = [child for child in children if child is not None]

    def _create_subtree(self, parent, subtree):
        if isinstance(subtree, tuple): # Inner Node
            if len(subtree) == 0: # Empty Tree
                return None
            elif len(subtree) == 2: # Attribute
                parent.attributes[subtree[0]]=subtree[1]
                return None # Wasn't a Child
            elif isinstance(subtree[1], str): # Group with Title
                new_parent = Group(subtree[0], subtree[1], *subtree[2:])
            else: # Group without title
                new_parent = Group(subtree[0], *subtree[1:])
            children = list()
            for c in new_parent.children:  # Add Children to Group
                children.append(self._create_subtree(new_parent, c))
            new_parent.children = [child for child in children if child is not None]
            return new_parent
        else: # Leaf (Table)
            if isinstance(subtree, Table):
                self.tables.append(subtree)
            elif isinstance(subtree, Array):
                self.arrays.append(subtree)
            return subtree

    def __repr__(self):
        return repr(self.tree)

    def __str__(self):
        return str(self.tree)

    def save_dot(self, fname):
        f = open(fname, 'w')
        f.write(self.dot())
        f.close()

    def show_dot(self):
        #make temp file
        import os
        f = open('./temp.gv', 'w')
        f.write(self.dot())
        f.close()
        os.system('dot -Tps ./temp.gv -o ./temp.ps')
        os.system('gnome-open ./temp.ps')


    def _dot_visit(self, node):
        self.dot_text += node.dot()

    def dot(self):
        self.dot_text = 'digraph "%s" {\n' % self.name
        self.dot_text += 'labelfontname=Helvetica;\n'
        self._preorder(self.root, self._dot_visit)
        self.dot_text += '}'
        return self.dot_text

    def _preorder(self, root, visit):
        visit(root)
        if isinstance(root, Group):
            for child in root.children:
                self._preorder(child, visit)

t = ('inner_num_%d' % 2, 'd',
          ('tseng', 'd',
                ('bbcalculator', 'dd',
                    Table('params', 'parameters',
                        net=str,
                        arch=str,
                        run_count=int),
                    Table('state', 'attrs',
                        cost=float,
                        mod_seed=int,
                        swap_seed=int,
                        moves_since_cost_recompute=int,
                        rlim=float,
                        temp=float,
                        temp_stage=int,
                        run_count=int,
                        xdim=int,
                        ydim=int,
                        runtime=float,
                        index=int,
                        sum_of_squares=float,
                        average_cost=float,
                        move_count=int),
                    Table('stage_transitions', 'temp',
                        stage_id=int,
                        id_=int))))


if __name__ == "__main__":
    T = Table('Person', "Describes a person in a table",
            name=(str, 'Last, First'),
            birthday=(tuple, 'Day Month Year'),
            age=int)
    Tr = Tree('root', 'vpr96tree', t)#Tree('Root', 'description', ('hehe', "100"), T, ('Child2', "Description", Table('Child', "A child of parent", name=str)))
    Tr.save_dot('./dot.gv')
    print Tr.dot()
    Tr.show_dot()
