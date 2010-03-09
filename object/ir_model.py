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

class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        """
        Extend this method to retrieve the model and these inherits
        """
        if context.get('import'):
            model_obj = self.pool.get('ir.model')
            model = model_obj.read(cr, uid, args[0][2], ['model'])
            inherits = self.pool.get(model['model'])._inherits
            if inherits:
                mod_ids = [args[0][2]]
                for m in inherits:
                    mod_id = model_obj.search(cr, uid, [('model','=', m)])
                    mod_ids.append(mod_id[0])
                args = [('model_id','in', mod_ids)]
        return super(ir_model_fields, self).name_search(cr, uid, name, args, operator, context, limit)

ir_model_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
