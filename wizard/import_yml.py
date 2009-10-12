# -*- coding: utf-8 -*-
##############################################################################
#
#    document_csv module for OpenERP
#    Copyright (C) 2009 SYLEAM (<http://www.syleam.fr>) Christophe CHAUVET
#
#    This file is a part of document_csv
#
#    document_csv is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    document_csv is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import wizard
import pooler
from cStringIO import StringIO
import base64
import yaml

init_form = """<?xml version="1.0" ?>
<form string="Import CSV structure">
  <separator string="Select file to import" colspan="4"/>
  <field name="filename" colspan="4" width="300"/>
</form>
"""

init_fields = {
    'filename': {'string':'Select File', 'type':'binary','required':True,'filters':'*.yml'},
}

def _import(self, cr, uid, data, context):
    if not context: context = {}
    print 'DATA: %r' % data

    return {}

class import_yaml(wizard.interface):

    states = {
        'init' : {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': init_form,
                'fields': init_fields,
                'state': [('end','Cancel','gtk-cancel'), ('valid', 'OK', 'gtk-ok', True)],
            }
        },
        'valid': {
            'actions': [_import],
            'result': {
                'type': 'state',
                'state': 'end'
            }
        }
    }

import_yaml('document_csv.import')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
