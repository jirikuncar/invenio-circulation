# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Circulation API."""

from functools import partial, wraps

from flask import current_app
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records_files.api import Record
from werkzeug.local import LocalProxy


current_jsonschemas = LocalProxy(
    lambda: current_app.extensions['invenio-jsonschemas']
)


def has_status(method=None, status='draft'):
    """Check that deposit has defined status (default: draft)."""
    if method is None:
        return partial(has_status, status=status)

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Check current deposit status."""
        if status != self['_circulation']['status']:
            raise PIDInvalidAction()

        return method(self, *args, **kwargs)
    return wrapper


def preserve(method=None, result=True, fields=None):
    """Preserve fields in deposit."""
    if method is None:
        return partial(preserve, result=result, fields=fields)

    fields = fields or ('_circulation', )

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Check current deposit status."""
        data = {field: self[field] for field in fields if field in self}
        result_ = method(self, *args, **kwargs)
        replace = result_ if result else self
        for field in data:
            replace[field] = data[field]
        return result_
    return wrapper


class Location(Record):
    """Define API for managing locations."""

    @classmethod
    def create(cls, data, id_=None):
        """Create a location instance and store it in database."""
        data = data or {}
        schema = current_app.config.get('CIRCULATION_LOCATION_SCHEMA', None)
        if schema:
            data.setdefault('$schema', schema)
        return super(Location, cls).create(data, id_=id_)


class Item(Record):
    """Define API for managing locations."""

    @classmethod
    def create(cls, data, id_=None):
        """Create a location instance and store it in database."""
        data = data or {}
        schema = current_app.config.get('CIRCULATION_ITEM_SCHEMA', None)
        if schema:
            data.setdefault('$schema', schema)
        # TODO create model (enum) with states
        data.setdefault('_circulation', {'status', 'on_shelf'})
        return super(Item, cls).create(data, id_=id_)

    @property
    def overdue(self):
        """Check if the item is overdue."""
        raise NotImplemented()

    #
    # Define transition methods bellow.
    #
    def borrow(self, user):
        """Borrow this item to a user."""
        raise NotImplemented

    def return_(self):
        """Return this item by a user."""
        # TODO is it returned by same user that has borrowed the item?
        raise NotImplemented()
