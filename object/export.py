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
from StringIO import StringIO
from tools import ustr

class export_csv(osv.osv):
    """
    CSV File export description
    """
    _name = 'document.export.csv'
    _description = 'CSV Export definition'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'ctx': fields.char('Context', size=256),
        'dom': fields.char('Domain', size=256),
        'inc_header': fields.boolean('Include header'),
        'last_sep': fields.boolean('Include last separator'),
        'line_ids': fields.one2many('document.export.csv.line', 'export_id', 'Lines'),
    }

    _defaults = {
        'ctx': lambda *a: '{}',
        'dom': lambda *a: '[]',
        'inc_header': lambda *a: False,
        'last_sep': lambda *a: False,
    }

    def onchange_domain(self, cr, uid, ids, val, context=None):
        if not context: context = {}
        warning = {}
        warning['title'] = _('Error')
        warning['message'] = _('Bad domain value')
        if ids and not val == '{}':
            try:
                val = eval(val)
                if not isinstance(val, list):
                    return {'warning': warning}
            except SyntaxError, e:
                warning['message'] = _('Syntax error\n* %r') % e
                return {'warning': warning}
            except TypeError, e:
                warning['message'] = _('The domain must be start with [ and ending with ]\n* %r') % e
                return {'warning': warning}

        return {'warning': False}

    def onchange_context(self, cr, uid, ids, val, context=None):
        if not context: context = {}
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

export_csv()

class export_csv_line(osv.osv):
    """
    CSV Line to export
    """
    _name = 'document.export.csv.line'
    _description = 'CSV export line definition'

    _columns = {
        'name': fields.char('Name', size=128, required=True, help='Column name'),
        'field_id': fields.many2one('ir.model.fields', 'Field', required=True),
        'sequence': fields.integer('Sequence'),
        'export_id': fields.many2one('document.export.csv', 'Export', required=True),
    }

    _defaults = {
        'sequence': lambda *a: 10,
    }

export_csv_line()

class document_directory_content(osv.osv):
    _inherit = 'document.directory.content'
    _columns = {
        'csv_export_def': fields.many2one('document.export.csv', 'CSV Structure', help='Export CSV file'),
    }

    def process_read_csv(self, cr, uid, node, context=None):
        """
        This function generate the CSV file
        """
        if not context: context = {}
        obj_export = node.content.csv_export_def
        ctx = context.copy()
        ctx.update(eval(obj_export.ctx))
        domain = eval(obj_export.dom)
        obj_class = self.pool.get(obj_export.model_id.model)
        separator = ';'

        fields = obj_class.fields_get(cr, uid, None, context=context)
        print 'FIELDS: %r' % fields
        ids = obj_class.search(cr, uid, domain, context=context)
        all = ''

        # add header in the first line
        if obj_export.inc_header:
            for fld in obj_export.line_ids:
                all += '"%s"%s' % (fld.name, separator)
            if not obj_export.last_sep:
                all = all[:-1]
            all += '\n'

        # For each lines, extract the content, and replace it if required
        for obj in obj_class.browse(cr, uid, ids, context=context):
            for fld in obj_export.line_ids:
                print 'FLD: %r' % fld.field_id.name
                value = getattr(obj, fld.field_id.name)
                value = value and ustr(value)
                if type(value) == type(obj):
                    # TODO: use name_get
                    value = value.name

                #print 'VALUES: %r' % value
                res = ''
                print 'TYPE: %r' % type(value)
                if fields[fld.field_id.name]['type'] in ('char','text','selection'):
                    #if isinstance(value, (str,unicode)):
                    res = '"%s"' % (value or '')
                else:
                    res = '%s' % value

                all += '%s%s' % (res, separator)

            if not obj_export.last_sep:
                all = all[:-1]
            all += '\n'

        s = StringIO(all.encode('utf-8'))
        s.name = node
        return s

document_directory_content()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
