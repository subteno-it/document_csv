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

"""
Add the possibility to export dynamically a CSV file
"""

import locale
import time
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
        'id_use': fields.boolean('Use ID', help='Check this if you want to add id in the first columns'),
        'id_emu': fields.boolean('Emulate ID', help="Check this, if you want to generate ID if it doesn't exist in the database"),
        'line_ids': fields.one2many('document.export.csv.line', 'export_id', 'Lines'),
    }

    _defaults = {
        'ctx': lambda *a: '{}',
        'dom': lambda *a: '[]',
        'inc_header': lambda *a: False,
        'last_sep': lambda *a: False,
        'id_use': lambda *a: False,
        'id_emu': lambda *a: False,
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
        if not context: context = node.context
        obj_export = node.content.csv_export_def
        ctx = context.copy()
        # If lang is not set, retrieve it form user form
        ctx['lang'] = self.pool.get('res.users').read(cr, uid, [uid], ['context_lang'])[0]['context_lang']
        ctx.update(eval(obj_export.ctx))
        domain = eval(obj_export.dom)
        obj_class = self.pool.get(obj_export.model_id.model)
        obj_imd = self.pool.get('ir.model.data')
        separator = ';'

        fields = obj_class.fields_get(cr, uid, None, context=context)
        ids = obj_class.search(cr, uid, domain, context=context)
        all = ''

        # add header in the first line
        if obj_export.inc_header:
            if obj_export.id_use:
                all += '"ID"'
            for fld in obj_export.line_ids:
                all += '"%s"%s' % (fld.name, separator)
            if not obj_export.last_sep:
                all = all[:-1]
            all += '\n'

        # inherit the locale to use the user one
        loc = locale.getlocale()
        lc_all = '%s.UTF-8' % ctx.get('lang', 'en_US')
        locale.setlocale(locale.LC_ALL, lc_all.encode('utf-8'))

        # For each lines, extract the content, and replace it if required
        for obj in obj_class.browse(cr, uid, ids, context=context):
            if obj_export.id_use:
                res_id = obj_imd.search(cr, uid, [('model', '=', obj_export.model_id.model), ('res_id', '=', obj.id)], context=context)
                if res_id:
                    res = obj_imd.read(cr, uid, res_id, ['module','name'], context=context)[0]
                    if not res['module']:
                        all += '"%s"%s' % (res['name'], separator)
                    else:
                        all += '"%s.%s"%s' % (res['module'], res['name'], separator)
                else:
                    if obj_export.id_emu:
                        all += '"%s_%d"%s' % (obj_export.model_id.model.replace('.','_'), obj.id, separator)
                    else:
                        all += '""%s' % separator
            for fld in obj_export.line_ids:
                value = getattr(obj, fld.field_id.name)
                ftype = fields[fld.field_id.name]['type']
                if ftype == 'many2one':
                    ng = self.pool.get(fields[fld.field_id.name]['relation']).name_get(cr, uid, value.id, context=context)
                    value = False
                    if len(ng):
                        value = ng[0][1]

                res = ''
                if ftype in ('char','text','selection','many2one'):
                    #if isinstance(value, (str,unicode)):
                    res = '"%s"' % (value or '')
                elif ftype == 'date' and value:
                    res = '%s' % time.strftime(locale.nl_langinfo(locale.D_FMT) ,time.strptime(value, '%Y-%m-%d'))
                elif ftype == 'datetime' and value:
                    res = '%s' % time.strftime(locale.nl_langinfo(locale.D_T_FMT) ,time.strptime(value, '%Y-%m-%d %H:%M:%S'))
                else:
                    res = '%s' % (value or '')

                all += '%s%s' % (res, separator)

            if not obj_export.last_sep:
                all = all[:-1]
            all += '\n'

        # restore the original locale setting
        locale.setlocale(locale.LC_ALL, loc)

        s = StringIO(all.encode('utf-8'))
        s.name = node
        return s

document_directory_content()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
