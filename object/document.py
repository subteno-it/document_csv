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

from osv import osv
from osv import fields
from tools.translate import _
import time

_encoding = [
    ('utf-8', 'UTF 8'),
    ('cp850', 'CP 850 IBM'),
    ('iso8859-1','Latin 1'),
    ('iso8859-15','Latin 9'),
]

class import_list(osv.osv):
    _name='document.import.list'
    _description = 'Document importation list'

    _columns = {
        'model_id': fields.many2one('ir.model','Model', required=True),
        'domain': fields.char('Domain', size=256),
        'context': fields.char('Context', size=256, help='this part complete the original context'),
        'filename': fields.char('Backup filename', size=128, required=True, help='Indique the name of the file to backup, use:\n%%Y for year\n%%m for month'),
        'disable': fields.boolean('Disable', help='Uncheck this, if you want to disable it'),
        'err_mail': fields.boolean('Send log by mail', help='The log file was send to all users of the groupes'),
        'err_reject': fields.boolean('Reject all if error', help='Reject all lines if there is an error'),
        'group_id': fields.many2one('res.groups', 'Group', help='Group use for sending email'),
        'csv_sep': fields.char('Separator', size=1, required=True),
        'csv_esc': fields.char('Escape', size=1),
        'encoding': fields.selection(_encoding, 'Encoding'),
        'line_ids': fields.one2many('document.import.list.line','list_id', 'Lines'),
        'directory_id': fields.many2one('document.directory','Directory', required=True, help='Select directory where the file was put'),
        'backup_dir_id': fields.many2one('document.directory','Backup directory', required=True, help='Select directory where the backup file was put'),
    }

    _defaults = {
        'domain': lambda *a: '[]',
        'context': lambda *a: '{}',
        'disable': lambda *a: True,
        'csv_sep': lambda *a: ';',
        'csv_esc': lambda *a: '"',
    }

    def onchange_context(self, cr, uid, ids, val, context=None):
        if not context: context = {}
        warning = {}
        warning['title'] = _('Error')
        warning['message'] = _('Bad context value')
        try:
            val = eval(val)
            if not isinstance(val, dict):
                return {'warning': warning}
        except SyntaxError, e:
            print '%s' % e
            warning['message'] = _('Syntax error')
            return {'warning': warning}
        except TypeError, e:
            warning['message'] = _('The context must be start with { and ending with }\n* %s') % e
            return {'warning': warning}

        return {'warning': False}

import_list()

class import_list_line(osv.osv):
    _name='document.import.list.line'
    _description='Document importation list line'

    _columns = {
        'list_id': fields.many2one('document.import.list', 'Line', required=True),
        'name': fields.char('Field name', size=128, required=True),
        'field_id': fields.many2one('ir.model.fields', 'Field', required=True),
        'relation': fields.char('Field relation', size=64, help='Specify which field is used to match this field in relation'),
        'uniq': fields.boolean('Uniqueness', help='If check, the field relation must be unique'),
        'create': fields.boolean('Create entry', help="If check, if entry doesn't exist, it must be created"),
        'context': fields.char('Context', size=256),
        'refkey': fields.boolean('Reference Key', help='If check, this key is equal to ID in manual import'),
    }

import_list_line()

class ir_attachment(osv.osv):
    """Inherit this class to made the CSV treatment"""
    _inherit = 'ir.attachment'

    def create(self, cr, uid, vals, context=None):
        if not context: context={}
        res = super(ir_attachment, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if not context: context={}
        res = super(ir_attachment, self).write(cr, uid, ids, vals, context)
        print '-------\nWRITE %r\n----' % vals
        if res:
            # the file are store successfully, we can 
            # for each file import, check if there insert in
            # import directory
            model_obj = self.pool.get('ir.model')
            field_obj = self.pool.get('ir.model.fields')
            import_obj = self.pool.get('document.import.list')
            line_obj = self.pool.get('document.import.list.line')
            for f in ids:
                dir_id = self.read(cr, uid, ids, ['parent_id'], context=context)[0]['parent_id'][0]

                args = [('disable','=',False), ('directory_id','=', dir_id)]
                imp_ids = import_obj.search(cr, uid, args, context=context)
                print 'IMP_IDS: %r' % imp_ids
                if imp_ids:
                    import csv
                    import base64
                    from StringIO import StringIO
                    imp_data = import_obj.browse(cr, uid, imp_ids[0], context=context)
                    context.update(eval(imp_data.context))

                    imp = model_obj.read(cr, uid, imp_data.model_id.id, context=context)
                    model = imp['model']
                    # Read all field name in the list
                    fld=[]
                    for l in imp_data.line_ids:
                        line = line_obj.browse(cr, uid, [l.id], context=context)[0]
                        print 'Line: %s (%r)' % (line.name, line.field_id.name)
                        args = {
                            'name': line.name, 
                            'field': line.field_id.name,
                            'type': line.field_id.ttype,
                            'relation': line.field_id.relation,
                            'key': line.refkey,
                        }
                        fld.append(args)

                    # Compose the header
                    header = []
                    for h in fld:
                        if h['type'] not in ('many2one','one2many','many2many'):
                            header.append(h['field'])
                        else:
                            print 'Not implemented'

                    print 'Header: %r' % header

                    # Compose the line from the csv import
                    lines = []

                    val = ''
                    if 'datas' in vals:
                        val = base64.decodestring(vals['datas'])
                    print 'VAL: %r' % val

                    fp = StringIO()
                    fp.write(val)
                    sep = chr(ord(imp_data.csv_sep[0]))
                    esc=None
                    if imp_data.csv_esc:
                        esc = chr(ord(imp_data.csv_esc[0]))

                    csvfile = csv.DictReader(fp, delimiter=sep)
                    print 'CSVFILE: %r' % csvfile
                    for c in csvfile:
                        print 'TEST 1'
                        print 'FIELD: %r' % c
                        tmpline = []
                        for f in fld:
                            tmpline[f['field']] = c[f['name']]
                        lines.append(tmpline)

                    # After treatment, close th StringIO
                    fp.close()
                    print 'LINES: %r' % lines

                    print 'Objet: %r' % imp_data.model_id.model
                    obj = self.pool.get(imp_data.model_id.model).import_data(cr, uid, header, lines, 'init', '', False, context=context)

                    print 'Archivage'
                    self.write(cr, uid, ids, {'name': time.strftime(imp_data.filename), 'parent_id': imp_data.backup_dir_id.id}, context=context)
        return res

ir_attachment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
