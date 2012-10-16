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

from osv import osv


class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'

    def search_inherits(self, cr, uid, model_id, context=None):
        """
        For a model, retrieve it inherits fields
        """
        if context is None:
            context = {}

        if isinstance(model_id, list):
            model_id = model_id[0]

        model_obj = self.pool.get('ir.model')
        inherits = self.pool.get(model_obj.read(cr, uid, model_id, ['model'])['model'])._inherits
        mod_ids = [model_id]
        if inherits:
            mod_ids.extend(model_obj.search(cr, uid, [('model', 'in', inherits.keys())]))
        return mod_ids

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        Search must be include inherits
        """
        if context is None:
            context = {}

        if context.get('import'):
            model_id = [x[2] for x in args if x[0] == 'model_id']
            if not model_id:
                return super(ir_model_fields, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

            mod_ids = self.search_inherits(cr, uid, model_id[0], context=context)
            args = [x for x in args if x[0] != 'model_id']
            args.append(('model_id', 'in', mod_ids))
        return super(ir_model_fields, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        """
        Extend this method to retrieve the model and these inherits
        """
        if context is None:
            context = {}

        if context.get('import'):
            model_id = [x[2] for x in args if x[0] == 'model_id']
            if not model_id:
                return super(ir_model_fields, self).name_search(cr, uid, name, args, operator, context, limit)

            mod_ids = self.search_inherits(cr, uid, model_id[0], context=context)
            args = [('model_id', 'in', mod_ids)]
        return super(ir_model_fields, self).name_search(cr, uid, name, args, operator, context, limit)

ir_model_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
