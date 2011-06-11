# -*- coding: utf-8 -*-
##############################################################################
#
#    document_csv module for OpenERP, Import structure in CSV
#    Copyright (C) 2011 SYLEAM (<http://www.syleam.fr/>) 
#              Christophe CHAUVET <christophe.chauvet@syleam.fr>
#
#    This file is a part of document_csv
#
#    document_csv is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    document_csv is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields

class LaunchImport(osv.osv_memory):
    _name = 'wizard.launch.import.csv'
    _description = 'Interface to launch CSV import'
    _rec_name = 'import_list'

    def _import_list(self, cr, uid, context=None):
        implist_obj = self.pool.get('document.import.list')
        doc_ids = implist_obj.search(cr, uid, [('disable', '=', False)])
        if doc_ids:
            return [(x.id, x.name) for x in implist_obj.browse(cr, uid, doc_ids)]
        return []

    _columns = {
        'import_list': fields.selection(_import_list, 'List', help='List of available import structure', required=True),
        'import_file': fields.binary('Filename', required=True),
        'email_result': fields.char('Email', size=256, help='Email to send notification when import is finished'),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        """
        Retrieve email for this user
        """
        if context is None:
            context = {}

        res = super(LaunchImport, self).default_get(cr, uid, fields_list, context=context)
        res['email_result'] = self.pool.get('res.users').browse(cr, uid, uid, context=context).user_email or ''
        return res
        

    def launch_import(self, cr, uid, ids, context=None):
        """
        Save file, and execute importation
        """
        cur = self.browse(cr, uid, ids[0], context=context)
        self.pool.get('ir.attachment').import_csv(cr, uid, cur.import_list, cur.import_file, cur.email_result, context=context)
        return {'type': 'ir.actions.act_window_close'}

LaunchImport()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
