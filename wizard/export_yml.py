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
from tools.translate import _

init_form = """<?xml version="1.0" ?>
<form string="Export structure">
  <separator string="The export file is available, save it to a local drive" colspan="4"/>
  <field name="name" invisible="1"/>
  <field name="filename" colspan="4" width="350" filename="name"/>
</form>
"""

init_fields = {
    'name': {'string': 'File name', 'type': 'char', 'size': 128},
    'filename': {'string':'Select a filename, and save it', 'type':'binary','required':True,'filters':'*.yml'},
}

def _init(self, cr, uid, data, context):
    if not context: context = {}
    try:
        import yaml
    except ImportError:
        raise wizard.except_wizard(_('Error'),_('Python Yaml Module not found, see description module'))
    pool = pooler.get_pool(cr.dbname)
    doc_obj = pool.get('document.import.list')
    doc = doc_obj.browse(cr, uid, data['id'], context=context)
    yml_file = '%s.yml' % doc.name.lower().replace(' ','_')
    content = {}
    content['name'] = doc.name
    content['object'] = doc.model_id.model
    content['directory'] = doc.directory_id.name
    content['context'] = doc.ctx
    content['separator'] = doc.csv_sep
    content['escape'] = doc.csv_esc
    content['encoding'] = doc.encoding
    lines = []
    for l in doc.line_ids:
        line = {}
        line['name'] = l.name
        line['field'] = l.field_id.name
        if l.field_id.ttype in ('many2one','many2many'):
            line['relation'] = l.relation
        line['refkey'] = l.refkey
        lines.append(line)
    content['lines'] = lines
    buf = StringIO()
    #print yaml.dump(content, default_flow_style=False)
    buf.write(yaml.dump(content, encoding='utf-8', default_flow_style=False))
    out = base64.encodestring(buf.getvalue())
    buf.close()
    return {'filename': out, 'name': yml_file}

class export_yaml(wizard.interface):

    states = {
        'init' : {
            'actions': [_init],
            'result': {
                'type': 'form',
                'arch': init_form,
                'fields': init_fields,
                'state': [('end','Cancel','gtk-cancel'), ('valid', 'OK', 'gtk-ok', True)],
            }
        },
        'valid': {
            'actions': [],
            'result': {
                'type': 'state',
                'state': 'end'
            }
        }
    }

export_yaml('document_csv.export')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
