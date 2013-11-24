# Copyright (c) 2013 Universidade Federal Fluminense (UFF), Polytechnic Institute of New York University.
# This file is part of noWorkflow. Please, consult the license terms in the LICENSE file.

import os.path
import hashlib
import sqlite3
import sys
from utils import print_msg
from pkg_resources import resource_string  #@UnresolvedImport

PROVENANCE_DIRNAME = '.noworkflow'
CONTENT_DIRNAME = 'content'
DB_FILENAME = 'db.sqlite'
DB_SCRIPT = 'resources/noworkflow.sql'

content_path = None  # Base path for storing content of files
db_conn = None  # Connection to the database
trial_id = None  # Id of the prospective provenance used in this trial

std_open = open  # Original Python open function.

def has_provenance(path):
    provenance_path = os.path.join(path, PROVENANCE_DIRNAME)
    return os.path.isdir(provenance_path)


def connect(path):
    global content_path, db_conn
    provenance_path = os.path.join(path, PROVENANCE_DIRNAME)
            
    content_path = os.path.join(provenance_path, CONTENT_DIRNAME)
    if not os.path.isdir(content_path):
        os.makedirs(content_path)

    db_path = os.path.join(provenance_path, DB_FILENAME)
    new_db = not os.path.exists(db_path)
    db_conn = sqlite3.connect(db_path)
    db_conn.row_factory = sqlite3.Row
    if new_db:
        print_msg('creating provenance database')
        with db_conn as db:
            db.executescript(resource_string(__name__, DB_SCRIPT))  # Accessing the content of a file via setuptools


def connect_existing(path):
    if not has_provenance(path):
        print_msg('there is no provenance store in the current directory', True)
        sys.exit(1)
    connect(path)

        
# CONTENT STORAGE FUNCTIONS
            
def put(content):
    content_hash = hashlib.sha1(content).hexdigest()
    content_dirname = os.path.join(content_path, content_hash[:2])
    if not os.path.isdir(content_dirname):
        os.makedirs(content_dirname)
    content_filename = os.path.join(content_dirname, content_hash[2:])
    if not os.path.isfile(content_filename):
        with std_open(content_filename, "wb") as content_file:
            content_file.write(content)
    return content_hash


def get(content_hash):
    content_filename = os.path.join(content_path, content_hash[:2], content_hash[2:])
    with std_open(content_filename, 'rb') as content_file:
        return content_file.read()


# DATABASE STORE/RETRIEVE FUNCTIONS
# TODO: Avoid replicating information in the DB. This will also help when diffing data.

def load(table_name, **condition):
    where = '1'
    for key in condition:
        where += ' and {} = {}'.format(key, condition[key]) 
    with db_conn as db:
        print 'select * from {} where {}'.format(table_name, where)
        return db.execute('select * from {} where {}'.format(table_name, where))


def insert(table_name, attrs, **extra_attrs):  # Not in use, but can be useful in the future
    query = 'insert into {}({}) values ({})'.format(table_name, ','.join(attrs.keys() + extra_attrs.keys()),','.join(['?'] * (len(attrs) + len(extra_attrs))))
    with db_conn as db:
        db.execute(query, attrs.values() + extra_attrs.values())
        

def insertmany(table_name, attrs_list, **extra_attrs):  # Not in use, but can be useful in the future
    for attrs in attrs_list:
        insert(table_name, attrs, **extra_attrs)


def last_trial_id():
    with db_conn as db:
        (an_id,) = db.execute("select id from trial where start in (select max(start) from trial)").fetchone()
    return an_id   


def last_trial_id_without_iheritance():
    with db_conn as db:
        (an_id,) = db.execute("select id from trial where start in (select max(start) from trial where inherited_id is NULL)").fetchone()
    return an_id   


def iherited_id(an_id):
    with db_conn as db:
        (iherited_id,) = db.execute("select inherited_id from trial where id = ?", (an_id,)).fetchone()
    return iherited_id


def store_trial(start, script, code, bypass_modules):
    global trial_id
    code_hash = put(code)
    iherited_id = last_trial_id_without_iheritance() if bypass_modules else None
    with db_conn as db: 
        trial_id = db.execute("insert into trial (start, script, code_hash, inherited_id) values (?, ?, ?, ?)", (start, script, code_hash, iherited_id)).lastrowid


def update_trial(finish, function_call):
    store_function_call(function_call, None)
    with db_conn as db:        
        db.execute("update trial set finish = ? where id = ?", (finish, trial_id))
        
        
def load_trial(an_id):
    global trial_id
    trial_id = an_id
    return load('trial', id = trial_id)
    

def store_dependencies(dependencies):
    data = [(name, version, path, code_hash, trial_id) for name, version, path, code_hash in dependencies]    
    with db_conn as db:
        db.executemany("insert into module(name, version, file, code_hash, trial_id) values (?, ?, ?, ?, ?)", data)

        
def load_dependencies():
    an_id = iherited_id(trial_id)
    if not an_id: an_id = trial_id
    return load('module', trial_id = an_id)


def store_environment(env_attrs):
    data = [(name, value, trial_id) for name, value in env_attrs.iteritems()]
    with db_conn as db:
        db.executemany("insert into environment_attr(name, value, trial_id) values (?, ?, ?)", data)
        

def store_objects(objects, obj_type, function_def_id):
    data = [(name, obj_type, function_def_id) for name in objects]
    with db_conn as db:
        db.executemany("insert into object(name, type, function_def_id) values (?, ?, ?)", data)    


def store_function_defs(functions):  
    with db_conn as db:
        for name, (arguments, global_vars, calls, code_hash) in functions.items():
            function_def_id = db.execute("insert into function_def(name, code_hash, trial_id) values (?, ?, ?)", (name, code_hash, trial_id)).lastrowid
            store_objects(arguments, 'ARGUMENT', function_def_id)
            store_objects(global_vars, 'GLOBAL', function_def_id)
            store_objects(calls, 'FUNCTION', function_def_id)
            
            
def store_file_accesses(file_accesses, function_call_id):
    with db_conn as db:
        for file_access in file_accesses:
            data = (file_access['name'], file_access['mode'], file_access['buffering'], file_access['content_hash_before'], file_access['content_hash_after'], file_access['timestamp'], function_call_id, trial_id)
            db.execute("insert into file_access(name, mode, buffering, content_hash_before, content_hash_after, timestamp, function_call_id, trial_id) values (?, ?, ?, ?, ?, ?, ?, ?)", data)
       

def store_object_values(object_values, obj_type, function_call_id):
    data = [(name, value, obj_type, function_call_id) for name, value in object_values.iteritems()]
    with db_conn as db:
        db.executemany("insert into object_value(name, value, type, function_call_id) values (?, ?, ?, ?)", data)    

  
def store_function_call(function_call, caller_id):
    data = (function_call['name'], function_call['line'], function_call['return'], function_call['start'], function_call['finish'], caller_id, trial_id)
    with db_conn as db:
        function_call_id = db.execute("insert into function_call(name, line, return, start, finish, caller_id, trial_id) values (?, ?, ?, ?, ?, ?, ?)", data).lastrowid
    store_object_values(function_call['arguments'], 'ARGUMENT', function_call_id)
    store_file_accesses(function_call['file_accesses'], function_call_id)
    for inner_function_call in function_call['function_calls']:
        store_function_call(inner_function_call, function_call_id)
        
