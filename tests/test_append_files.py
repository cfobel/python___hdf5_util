import tempfile
from subprocess import check_call, check_output

from path import path

from hdf5_util import tables, find_command
from hdf5_util.append_files import HDF5File


class Person(tables.IsDescription):
    first_name = tables.StringCol(64, pos=0)
    last_name = tables.StringCol(64, pos=1)
    age = tables.UInt8Col(pos=2)


def write_file(filepath, people_dicts):
    #filter_ = tables.Filters(complevel=1, complib='blosc')
    #h5f = tables.openFile(filepath, mode='w', filters=filter_)
    h5f = tables.openFile(filepath, mode='w')
    people = h5f.createTable(h5f.root, 'people', Person)
    people.append([[p['first_name'], p['last_name'], p['age']]
            for p in people_dicts])

    lucky_numbers = h5f.createVLArray(h5f.root, 'lucky_numbers',
            tables.UInt32Atom(dflt=0))
    for p in people_dicts:
        lucky_numbers.append(p['lucky_numbers'])
    h5f.close()


def test_append():
    people_dicts = [
        {'first_name': 'John', 'last_name': 'Doe', 'age': 32,
                'lucky_numbers': [7, 13, 93]},
        {'first_name': 'Jane', 'last_name': 'Doe', 'age': 28,
                'lucky_numbers': [7, 13, 93]},
        {'first_name': 'Someone', 'last_name': 'Else', 'age': 99,
                'lucky_numbers': [1, 0, 74]},]

    # Create a temporary directory to write working files to
    temp_dir = path(tempfile.mkdtemp(prefix='hdf5util__append_test'))

    try:
        # Create a separate HDF5 file for each person
        filepaths = []
        for person in people_dicts:
            filepath = temp_dir.joinpath('%s_%s.h5f' % (person['first_name'],
                    person['last_name']))
            write_file(filepath, [person])
            filepaths.append(path(filepath))

        appended_path = temp_dir.joinpath('combined-append_all.h5f')
        filepaths[0].copy(appended_path)
        hdf5_master = HDF5File(appended_path)

        # Combine generated HDF5 files into a single file
        for f in filepaths[1:]:
            hdf5_master.append_file(f)
        del hdf5_master

        # Write multiple 'person' entries to the same HDF5 file directly
        master_path = temp_dir.joinpath('combined.h5f')
        write_file(master_path, people_dicts)

        # Verify that the contents of the combined file are the same as
        # the contents of the file where all person entries are added
        # directly.
        h5diff_cmd = find_command('h5diff')
        check_call('%s %s %s' % (h5diff_cmd, master_path, appended_path),
                shell=True)
    finally:
        # Delete temp directory
        temp_dir.rmtree()
