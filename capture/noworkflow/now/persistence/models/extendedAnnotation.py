# Copyright (c) 2016 Universidade Federal Fluminense (UFF)
# Copyright (c) 2016 Polytechnic Institute of New York University.
# This file is part of noWorkflow.
# Please, consult the license terms in the LICENSE file.
"""ExtendedAnnotation Model"""
from __future__ import (absolute_import, print_function,
                        division, unicode_literals)

from datetime import datetime

import uuid
from future.utils import lmap
from future.builtins import map as cvmap
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy import ForeignKeyConstraint, select, bindparam

from ...utils.prolog import PrologDescription, PrologTrial
from ...utils.prolog import PrologRepr, PrologTimestamp

from .. import relational

from .base import AlchemyProxy, proxy_class, backref_one


def uuid_gen():
    return str(uuid.uuid4())
@proxy_class
class ExtendedAnnotation(AlchemyProxy):
    __tablename__ = "extendedAnnotation"
    id = Column( 
        String, unique=True, primary_key=True
    )
    __table_args__ = (
        ForeignKeyConstraint(["relatedExperiment"],
                             ["experiment.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["relatedTrial"],
                             ["trial.id"], ondelete="CASCADE")
    )
    annotation = Column(String)
    annotationFormat = Column(String)
    provenanceType = Column(String)
    annotationLevel = Column(String)
    relatedExperiment = Column(Text)
    relatedTrial = Column(Text)
  
    @classmethod  # query
    def create(cls, annt, session=None):
        
        # pylint: disable=too-many-arguments
        session = session or relational.session

        ant = cls.t
        id=uuid_gen()
        result = session.execute(
            ant.insert(),
            {"id": id, "annotation": annt.annotation, "annotationFormat": annt.annotationFormat,"provenanceType": annt.provenanceType, "annotationLevel": annt.annotationLevel, "relatedExperiment": annt.relatedExperiment,"relatedTrial": annt.relatedTrial})

        session.commit()
        annt.id=id
        return annt