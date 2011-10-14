# -*- coding: utf-8 -*-
##############################################################################
#
#    document_csv module for OpenERP
#    Copyright (C) 2009-2011 SYLEAM (<http://www.syleam.fr>) Christophe CHAUVET
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
import base64
import yaml
from tools.translate import _

init_form = """<?xml version="1.0" ?>
<form string="Import CSV structure">
  <field name="name" colspan="4"/>
  <separator string="Select file to import" colspan="4"/>
  <field name="filename" colspan="4" width="350"/>
</form>
"""

init_fields = {
    'filename': {'string': 'Select File', 'type': 'binary', 'required': True, 'filters': '*.yml'},
    'name': {'string': 'Name of the new import', 'type': 'char', 'size': 64, 'required': False},
}


def _import(self, cr, uid, data, context):
    if context is None:
        context = {}

    pool = pooler.get_pool(cr.dbname)
    model_obj = pool.get('ir.model')
    fld_obj = pool.get('ir.model.fields')
    dat_obj = pool.get('ir.model.data')
    dir_obj = pool.get('document.directory')
    imp_obj = pool.get('document.import.list')
    act_obj = pool.get('ir.actions.act_window')

    context['import'] = True

    content = base64.decodestring(data['form']['filename'])
    st = yaml.load(content)

    # Search the model_id
    mod_ids = model_obj.search(cr, uid, [('model', '=', st['object'])])
    if not mod_ids:
        raise wizard.except_wizard(_('Error'),
                _('No model name %s found') % st['object'])
    mod_id = mod_ids[0]
    imp = {
        'name': data['form']['name'] or st['name'],
        'ctx': st['context'],
        'model_id': mod_id,
        'csv_sep': st.get('separator', ';'),
        'csv_esc': st.get('escape', '"'),
        'encoding': st.get('encoding', 'utf-8'),
    }
    if st.get('version', '0.0') >= '1.1':
        imp['err_reject'] = st.get('reject_all', False)
        imp['log_filename'] = st.get('log_filename', False)
        imp['reject_filename'] = st.get('reject_filename', False)
        imp['backup_filename'] = st.get('backup_filename', False)

    if st.get('version', '0.0') >= '1.2':
        imp['notes'] = st.get('notes', False)
        imp['lang'] = st.get('lang', 'en_US')
        imp['err_mail'] = st.get('send_mail', False)
        imp['mail_from'] = st.get('mail_from', False)
        imp['mail_cc'] = st.get('mail_cc', False)
        imp['mail_subject'] = st.get('mail_subject', False)
        imp['mail_body'] = st.get('mail_body', False)
        imp['mail_cc_err'] = st.get('mail_cc_err', False)
        imp['mail_subject_err'] = st.get('mail_subject_err', False)
        imp['mail_body_err'] = st.get('mail_body_err', False)

    if st.get('version', '0.0') >= '1.3':
        imp['key_field_name'] = st.get('key_field_name', False)

    lines_ids = []
    for i in st['lines']:
        # The field id associate to the name
        fld_ids = fld_obj.search(cr, uid, [('model_id', '=', mod_id), ('name', '=', i['field'])], context=context)
        if not fld_ids:
            raise wizard.except_wizard(_('Error'), _('No field %s found in the object') % i['field'])

        l = {
            'name': i['name'],
            'field_id': fld_ids[0],
            'relation': i.get('relation', False),
            'refkey': i.get('refkey', False),
        }
        if i.get('model') and i.get('model') not in ('None', 'False'):
            mod_ids = model_obj.search(cr, uid, [('model', '=', i['model'])])
            if not mod_ids:
                raise wizard.except_wizard(_('Error'),
                                   _('No model name %s found') % i['model'])

            l['model_relation_id'] = mod_ids[0]
        if i.get('model_field') and i.get('model_field') not in ('None', 'False'):
            fld_ids = fld_obj.search(cr, uid, [('model_id', '=', mod_ids[0]), ('name', '=', i['model_field'])])
            if not fld_ids:
                raise wizard.except_wizard(_('Error'), _('No field %s found in the object') % i['model_field'])
            l['field_relation_id'] = fld_ids[0]

        lines_ids.append((0, 0, l))
    imp['line_ids'] = lines_ids

    imp_id = imp_obj.create(cr, uid, imp, context=context)
    if not imp_id:
        raise wizard.except_wizard(_('Error'), _('Failed to create the list entry'))

    result = dat_obj._get_id(cr, uid, 'document_csv', 'action_document_import_list')
    id = dat_obj.read(cr, uid, result, ['res_id'])['res_id']
    result = act_obj.read(cr, uid, id)
    result['domain'] = "[('id','in', [" + ','.join(map(str, [imp_id])) + "])]"
    return result


class import_yaml(wizard.interface):

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': init_form,
                'fields': init_fields,
                'state': [('end', 'Cancel', 'gtk-cancel'), ('valid', 'OK', 'gtk-ok', True)],
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
