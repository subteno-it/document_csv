# -*- coding: utf-8 -*-
##############################################################################
#
#    document_csv module for OpenERP
#    Copyright (C) 2009-2011 SYLEAM (<http://www.syleam.fr>) Christophe CHAUVET
#    Copyright (C) 2011 Camptocamp (http://www.camptocamp.com)
#              Guewen Baconnier
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

from osv import osv
from osv import fields
from tools.translate import _
import logging

_logger = logging.getLogger('document_csv')


class import_format(osv.osv):
    _name = 'document.import.format'
    _description = 'Define date and number format'

    help_name = """This field content depend to the type, see legend"""

    type_list = [
        ('date', 'Date'),
        ('time', 'Time'),
        ('datetime', 'DateTime'),
    ]

    _columns = {
        'name': fields.char('Format', size=64, required=True, help=help_name),
        'type': fields.selection(type_list, 'Type', help='Select the type of the format'),
    }
    _defaults = {
        'type': lambda *a: 'date',
    }

import_format()

# TODO retrieve list of encoding from locale library
_encoding = [
    ('ascii', 'ASCII'),
    ('utf-8', 'UTF 8'),
    ('cp1252', 'CP 1252 Windows'),
    ('cp850', 'CP 850 IBM'),
    ('iso8859-1', 'Latin 1'),
    ('iso8859-15', 'Latin 9'),
]


class import_list(osv.osv):
    _name = 'document.import.list'
    _description = 'Document importation list'
    _order = 'disable'

    def _get_format(self, cr, uid, name, context=None):
        fmt_obj = self.pool.get('document.import.format')
        ids = fmt_obj.search(cr, uid, [('type', '=', name)])
        res = [('', '')]
        for t in fmt_obj.browse(cr, uid, ids, context=context):
            res.append((t.id, t.name))
        return res

    def _get_format_date(self, cr, uid, context=None):
        if context is None:
            context = {}

        return self._get_format(cr, uid, 'date', context)

    def _get_format_time(self, cr, uid, context=None):
        if context is None:
            context = {}

        return self._get_format(cr, uid, 'time', context)

    def _get_format_datetime(self, cr, uid, context=None):
        if context is None:
            context = {}

        return self._get_format(cr, uid, 'datetime', context)

    _columns = {
        'name': fields.char('Import name', size=128, required=True),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'ctx': fields.char('Context', size=256, help='this part complete the original context'),
        'disable': fields.boolean('Disable', help='Check this, if you want to disable it'),
        'err_mail': fields.boolean('Send log by mail', help='The log file was send to all users of the groupes'),
        'err_reject': fields.boolean('Reject all if error', help='Reject all lines if there is an error'),
        'csv_sep': fields.char('Separator', size=1, required=True),
        'csv_esc': fields.char('Escape', size=1),
        'lang_id': fields.many2one('res.lang', 'Language', help='Language use in this import, to convert correctly date and float'),
        'encoding': fields.selection(_encoding, 'Encoding'),
        'line_ids': fields.one2many('document.import.list.line', 'list_id', 'Lines'),
        'backup_filename': fields.char('Backup filename', size=128, required=True, help='Indique the name of the file to backup, see legend at bottom'),
        'backup_dir_id': fields.many2one('document.directory', 'Backup directory', required=True, help='Select directory where the backup file was put'),
        'reject_filename': fields.char('Reject filename', size=128, required=True, help='Indique the name of the reject file, see legend at bottom'),
        'reject_dir_id': fields.many2one('document.directory', 'Reject directory', required=True, help='Select the directory wher the reject file was put'),
        'log_filename': fields.char('Log filename', size=128, required=True, help='Indique the name of the log file, see legend at bottom'),
        'log_dir_id': fields.many2one('document.directory', 'Log directory', required=True, help='Select directory where the backup file was put'),
        'backup': fields.boolean('Store the backup', help='If check, the original file is backup, before remove from the directory'),
        'mail_from': fields.char('CC', size=128, help='Add cc mail, separate by comma'),
        'mail_cc': fields.char('CC', size=128, help='Add cc mail, separate by comma'),
        'mail_subject': fields.char('Subject', size=128, help='You can used format to the subject'),
        'mail_body': fields.text('Body'),
        'mail_cc_err': fields.char('CC', size=128, help='Add cc mail, separate by comma'),
        'mail_subject_err': fields.char('Subject', size=128, help='You can used format to the subject'),
        'mail_body_err': fields.text('Body'),
        'format_date': fields.many2one('document.import.format', 'Date', domain="[('type','=','date')]", help='Select the date format on the csv file'),
        'format_time': fields.many2one('document.import.format', 'Time', domain="[('type','=','time')]", help='Select the time format on the csv file'),
        'format_datetime': fields.many2one('document.import.format', 'DateTime', domain="[('type','=','datetime')]", help='Select the datetime format on the csv file'),
        'notes': fields.text('Note', help='Add note for this import '),
        'key_field_name': fields.char('Key column', size=64, help='The name of the column used as a key. If not filled, a key is generated from reference fields'),
    }

    _defaults = {
        'ctx': lambda *a: '{}',
        'disable': lambda *a: True,
        'csv_sep': lambda *a: ';',
        'csv_esc': lambda *a: '"',
        'backup_filename': lambda *a: 'sample-%Y%m%d_%H%M%S.csv',
        'reject_filename': lambda *a: 'sample-%Y%m%d_%H%M%S.rej',
        'log_filename': lambda *a: 'sample-%Y%m%d_%H%M%S.log',
        'notes': lambda *a: False,
    }

    def onchange_context(self, cr, uid, ids, val, context=None):
        if context is None:
            context = {}

        warning = {}
        warning['title'] = _('Error')
        warning['message'] = _('Bad context value')
        if ids and not val == '{}':
            try:
                val = eval(val)
                if not isinstance(val, dict):
                    return {'warning': warning}
            except SyntaxError, e:
                warning['message'] = _('Syntax error\n* %r') % e
                return {'warning': warning}
            except TypeError, e:
                warning['message'] = _('The context must be start with { and ending with }\n* %r') % e
                return {'warning': warning}

        return {'warning': False}

    def _prepare_structure_line(self, cr, uid, ids, field, context=None):
        """
        Prepare vals to write in document lines.
        @param field: browse instance of a field
        @return: dict of vals to write in the document for the field
        """
        import_line_obj = self.pool.get('document.import.list.line')
        line_vals = {
            'name': field.name,
            'field_id': field.id,
        }
        onchange_res = import_line_obj.onchange_model_field(cr, uid, [], field.id, context=context)
        line_vals.update(onchange_res['value'])
        return line_vals
    
    def generate_structure_from_model(self, cr, uid, ids, context=None):
        fields_obj = self.pool.get('ir.model.fields')
        ctx_import = context.copy()
        ctx_import.update({'import': True})
        for import_list in self.browse(cr, uid, ids, context=context):
            existing_fields_ids = [il_field.id for il_field in [l.field_id for l in import_list.line_ids]]
            all_fields_ids = fields_obj.search(cr, uid,
                [('model_id', '=', import_list.model_id.id),
                 ('readonly', '=', False)],
                context=ctx_import, order='name asc')
            # keep only non existing fields but keep the sort
            fields_to_add_ids = [f_id for f_id in all_fields_ids if f_id not in existing_fields_ids]

            lines = []
            for field in fields_obj.browse(cr, uid, fields_to_add_ids, context=context):
                line_vals = self._prepare_structure_line(cr, uid, ids, field, context=context)
                if line_vals:
                    lines.append((0, 0, line_vals))

            self.write(cr, uid, import_list.id,
                       {'line_ids': lines},
                       context=context)
        return True

import_list()


class import_list_line(osv.osv):
    """
    Describe each columns from the CSV file and affect to a field in object
    """
    _name = 'document.import.list.line'
    _description = 'Document importation list line'

    _columns = {
        'list_id': fields.many2one('document.import.list', 'Line', required=True, ondelete='cascade'),
        'name': fields.char('Field name', size=128, required=True),
        'field_id': fields.many2one('ir.model.fields', 'Field'),
        'model_relation_id': fields.many2one('ir.model', 'Relation Model'),
        'field_relation_id': fields.many2one('ir.model.fields', 'Relation Field'),
        'relation': fields.selection([('', ''), ('id', 'ID'), ('db_id', 'DB ID'), ('search', 'Search')], 'Field relation', help='Search use name_search to match the record'),
        'create': fields.boolean('Create entry', help="If check, if entry doesn't exist, it must be created"),
        'refkey': fields.boolean('Reference Key', help='If check, this key is equal to ID in manual import'),
    }

    _defaults = {
        'relation': lambda *a: '',
    }

    # When select field is a relation, force domain for related field
    def onchange_model_field(self, cr, uid, ids, field_id, context=None):
        """
        Check if field is a relation (many2one, one2many many2many)
        """
        if context is None:
            context = {}

        result = {}
        domain = {}
        if not field_id:
            result['model_relation_id'] = False
            result['field_relation_id'] = False
        else:
            field_obj = self.pool.get('ir.model.fields').browse(cr, uid, field_id, context=context)
            if field_obj.ttype in ('many2one', 'one2many', 'many2many'):
                res_ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', field_obj.relation)], context=context)
                if res_ids:
                    result['model_relation_id'] = res_ids[0]
                    result['field_relation_id'] = False
                    domain['field_relation_id'] = [('model_id', '=', res_ids[0])]
            else:
                result['model_relation_id'] = False
                result['field_relation_id'] = False

        return {'value': result, 'domain': domain}

import_list_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
