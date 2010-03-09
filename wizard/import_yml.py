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
<form string="Import CSV structure">
  <separator string="Select file to import" colspan="4"/>
  <field name="filename" colspan="4" width="350"/>
</form>
"""

init_fields = {
    'filename': {'string':'Select File', 'type':'binary','required':True,'filters':'*.yml'},
}

def _check_yaml(self, cr, uid, data, context):
    try:
        import yaml
    except ImportError:
        raise wizard.except_wizard(_('Error'),_('Python Yaml Module not found, see description module'))
    return {}


def _import(self, cr, uid, data, context):
    if not context: context = {}
    import yaml
    pool = pooler.get_pool(cr.dbname)
    model_obj = pool.get('ir.model')
    fld_obj = pool.get('ir.model.fields')
    dat_obj = pool.get('ir.model.data')
    dir_obj = pool.get('document.directory')
    imp_obj = pool.get('document.import.list')
    act_obj = pool.get('ir.actions.act_window')

    content = base64.decodestring(data['form']['filename'])
    st = yaml.load(content)

    # Search the model_id
    mod_ids = model_obj.search(cr, uid, [('model','=', st['object'])])
    if not mod_ids:
        raise wizard.except_wizard(_('Error'), 
                                   _('No model name %s found') % st['object'])
    mod_id = mod_ids[0]

    # Search the directory
    dir_ids = dir_obj.search(cr, uid, [('name','=',st['directory'])])
    if not dir_ids:
        # We create it, with source directory parent
        dat_id = dat_obj._get_id(cr, uid, 'document_csv', 'dir_root_import_source')
        if not dat_id:
            raise wizard.except_wizard(_('Error'), _('Source directory reference not found'))
        s_id = dat_obj.read(cr, uid, dat_id, ['res_id'])['res_id']
        dir_args = {
            'name': st['directory'],
            'parent_id': s_id,
            'user_id': 1,
            'type': 'directory',
        }
        dir_ids = [dir_obj.create(cr, uid, dir_args, context=context)]
    dir_id = dir_ids[0]
    #raise wizard.except_wizard(_('Cool'), _('Ok'))

    imp = {
        'name': st['name'],
        'ctx': st['context'],
        'model_id': mod_id,
        'directory_id': dir_id,
        'csv_sep': st.get('separator', ';'),
        'csv_esc': st.get('escape', '"'),
        'encoding': st.get('encoding', 'utf-8'),
    }
    if st.get('version', '0.0') == '1.1':
        imp['err_reject'] = st.get('reject_all', False)
        imp['log_filename'] = st.get('log_filename', False)
        imp['reject_filename'] = st.get('reject_filename', False)
        imp['backup_filename'] = st.get('backup_filename', False)

    lines_ids = []
    for i in st['lines']:
        # The field id associate to the name
        fld_ids = fld_obj.search(cr, uid, [('model_id', '=', mod_id),('name', '=', i['field'])])
        if not fld_ids:
            raise wizard.except_wizard(_('Error'), _('No field %s found in the object') % i['field'])
        fld_id = fld_ids[0]

        l = {
            'name': i['name'],
            'field_id': fld_id,
            'relation': i.get('relation', False),
            'refkey': i.get('refkey', False),
        }

        lines_ids.append((0, 0, l))
    imp['line_ids'] = lines_ids

    imp_id = imp_obj.create(cr, uid, imp, context=context)
    if not imp_id:
        raise wizard.except_wizard(_('Error'), _('Failed to create the list entry'))

    result = dat_obj._get_id(cr, uid, 'document_csv', 'action_document_import_list')
    id = dat_obj.read(cr, uid, result, ['res_id'])['res_id']
    result = act_obj.read(cr, uid, id)
    result['domain'] ="[('id','in', ["+','.join(map(str, [imp_id]))+"])]"
    return result


class import_yaml(wizard.interface):

    states = {
        'init' : {
            'actions': [_check_yaml],
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
                'type': 'action',
                'action': _import,
                'state': 'end'
            }
        }
    }

import_yaml('document_csv.import')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
