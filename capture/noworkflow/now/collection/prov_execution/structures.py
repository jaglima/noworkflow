# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""Data Structures"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

from copy import copy
from collections import namedtuple


AssignAccess = namedtuple("AssignAccess", "value dependency addr value_dep")


class Assign(namedtuple("Assign", "moment value dependency")):
    """Represent an assignment for further processing"""

    def __new__(cls, *args, **kwargs):
        self = super(Assign, cls).__new__(cls, *args, **kwargs)
        self.accesses = {}
        return self

    def sub(self, value, dependency):
        """Create a new Assign with the same access for propagation in
        multiple assignments"""
        assign = Assign(self.moment, value, dependency)
        assign.accesses = self.accesses
        return assign


class DependencyAware(object):
    """Store dependencies of an element"""

    def __init__(self, active=True, exc_handler=-1, code_id=None):
        self.dependencies = []
        self.extra_dependencies = []
        self.exc_handler = exc_handler
        self.code_id = code_id

        self.active = active

    def add(self, dependency):
        """Add dependency"""
        if self.active:
            self.dependencies.append(dependency)

    def add_extra(self, dependency):
        """Add extra dependency"""
        if self.active:
            self.extra_dependencies.append(dependency)

    def __bool__(self):
        return bool(self.dependencies) or bool(self.extra_dependencies)

    def clone(self, mode=None, extra_only=False):
        """Clone dependency aware and replace mode"""
        new_depa = DependencyAware()
        if not extra_only:
            for dep in self.dependencies:
                new_dep = copy(dep)
                new_dep.mode = mode or new_dep.mode
                new_depa.add(new_dep)
        for dep in self.extra_dependencies:
            new_dep = copy(dep)
            new_dep.mode = mode or new_dep.mode
            new_depa.add_extra(new_dep)
        new_depa.exc_handler = self.exc_handler
        new_depa.code_id = self.code_id
        return new_depa

    @classmethod
    def join(cls, depa_list):
        new_depa = DependencyAware(exc_handler=float('inf'))
        for e_depa in depa_list:
            new_depa.code_id = e_depa.code_id
            new_depa.exc_handler = min(
                new_depa.exc_handler,
                e_depa.exc_handler
            )

            for dep in e_depa.dependencies:
                new_depa.add(dep)
            for dep in e_depa.extra_dependencies:
                new_depa.add_extra(dep)
        return new_depa


class Dependency(object):
    """Represent a dependency"""

    def __init__(self, activation_id, evaluation_id, value, value_id, mode):
        self.activation_id = activation_id
        self.evaluation_id = evaluation_id
        self.value = value
        self.value_id = value_id
        self.mode = mode

        # Kind: extra information about dependency
        self.kind = None
        self.arg = None
        self.sub_dependencies = []

    def __repr__(self):
        evaluation = __noworkflow__.evaluations[self.evaluation_id]
        code_component = __noworkflow__.code_components[
            evaluation.code_component_id]
        return "{}({})".format(code_component.name, self.mode)


class Parameter(object):

    def __init__(self, name, code_id, is_vararg=False):
        self.name = name
        self.code_id = code_id
        self.is_vararg = is_vararg
        self.filled = False
        self.default = None

    def __repr__(self):
        return "{}".format(self.name)


class CompartmentDependencyAware(DependencyAware):
    """Store dependencies of a compartment element"""

    def __init__(self, active=True, exc_handler=-1, code_id=None):
        super(CompartmentDependencyAware, self).__init__(
            active=active,
            exc_handler=exc_handler,
            code_id=code_id,
        )
        self.key = None
        self.value = None

class CollectionDependencyAware(DependencyAware):
    """Store dependencies of a compartment element"""

    def __init__(self, active=True, exc_handler=-1, code_id=None):
        super(CollectionDependencyAware, self).__init__(
            active=active,
            exc_handler=exc_handler,
            code_id=code_id,
        )
        # list of tuples representing (item name, evaluation_id, time)
        self.items = []
