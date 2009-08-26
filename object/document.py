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
    }

import_list_line()

_encoding = [
    ('utf-8', 'UTF 8'),
    ('cp850', 'CP 850 IBM'),
    ('iso8859-1','Latin 1'),
]

class import_list(osv.osv):
    _name='document.import.list'
    _description = 'Document importation list'

    _columns = {
        'model_id': fields.many2one('ir.model','Model', required=True),
        'domain': fields.char('Domain', size=256),
        'context': fields.char('Context', size=256, help='this part complete the original context'),
        'filename': fields.char('Filename', size=128, required=True, help='Indique the name of the file, or regexp that math to the result'),
        'disable': fields.boolean('Disable', help='Uncheck this, if you want to disable it'),
        'err_mail': fields.boolean('Send log by mail', help='The log file was send to all users of the groupes'),
        'err_reject': fields.boolean('Reject all if error', help='Reject all lines if there is an error'),
        'group_id': fields.many2one('res.groups', 'Group', help='Group use for sending email'),
        'csv_sep': fields.char('Separator', size=1, required=True),
        'csv_esc': fields.char('Escape', size=1),
        'encoding': fields.selection(_encoding, 'Encoding'),
        'line_ids': fields.one2many('document.import.list.line','list_id', 'Lines'),
        'directory_id': fields.many2one('document.directory','Directory', required=True, help='Select directory where the file was put'),
    }

    _defaults = {
        'domain': lambda *a: '[]',
        'context': lambda *a: '{}',
        'disable': lambda *a: True,
        'csv_sep': lambda *a: ';',
        'csv_esc': lambda *a: '"',
    }

import_list()


class ir_attachment(osv.osv):
    """Inherit this class to made the CSV treatment"""
    _inherit = 'ir.attachment'

    def create(self, cr, uid, vals, context=None):
        if not context: context={}
        res = super(ir_attachment, self).create(cr, uid, vals, context)
        print '-----\nCREATE %r' % vals
        print 'CONTEXT %s' % context
        print 'RES %r' % res
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if not context: context={}
        res = super(ir_attachment, self).write(cr, uid, ids, vals, context)
        print '-------\nWRITE %r' % vals
        print 'RES %r' % res
        if res:
            # the file are store successfully, we can 
            # for each file import, check if there insert in
            # import directory
            data_obj = self.pool.get('ir.model.data')
            import_obj = self.pool.get('document.import.list')
            for f in ids:
                result = data_obj._get_id(cr, uid, 'document_csv', 'dir_root_import')
                attch_id = data_obj.read(cr, uid, result, ['res_id'])['res_id']
                print 'attch_id: %r' % attch_id
                dir_id = self.read(cr, uid, ids, ['parent_id'], context=context)[0]['parent_id'][0]
                print 'dir_id: %r' % dir_id
                #                if dir_id == attch_id: 
                #                    # This is a file to import
                #                    # search to see if file match with an import treatment
                #                    args = [('disable','=',False)]
                #                    imp_ids = import_obj.search(cr, uid, args, context=context)
                #                    if imp_ids:
                #                        import glob
                #                        imp_data = import_obj.read(cr, uid, imp_ids, context=context)
                #                        print 'IMP_DATA: %r' % imp_data
                #                        trt = []
                #                        for i in imp_data:
                #                            trt[i]={}
                #                            trt[i]['id'] = i['id']
                #                            trt[i]['filename'] = glob.glob(i['filename'])

        return res

ir_attachment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
