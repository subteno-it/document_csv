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
import base64
import csv
from tools.translate import _

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class ReadCsv(osv.osv_memory):
    _name = 'wizard.read.csv.file'
    _description = 'Read the CSV header and import it on the current structure'
    _rec_name = 'import_file'

    _columns = {
        'import_file': fields.binary('Filename', required=True),
    }

    def read_header(self, cr, uid, ids, context=None):
        """
        read the CSV header, and insert into the current structure
        """
        implist_obj = self.pool.get('document.import.list')
        model_field_obj = self.pool.get('ir.model.fields')
        implist = implist_obj.browse(cr, uid, context.get('active_id'), context=context)
        cur = self.browse(cr, uid, ids[0], context=context)
        fpcsv = StringIO(base64.decodestring(cur.import_file))
        fpcsv.seek(0)

        sep = chr(ord(implist.csv_sep[0]))
        esc = implist.csv_sep and chr(ord(implist.csv_esc[0])) or None

        try:
            csvfile = csv.reader(base64.decodestring(cur.import_file).splitlines(), delimiter=sep, quotechar=esc)
            res = []
            args = {}
            for c in csvfile:
                # If columns name id, we use at key
                find_id = [x for x in c if x == 'id']
                if find_id:
                    args['key_field_name'] = 'id'

                # if header have been made for importcsv (openobject-library), we can match all fields at 100%
                args['line_ids'] = []
                for x in c:
                    if x == 'id':
                        continue

                    cur_line = {'name': x}
                    field_split = x.split(':')
                    if len(field_split) == 1:
                        field_split = x.split('/')

                    model_inherits = model_field_obj.search_inherits(cr, uid, implist.model_id.id, context=context)
                    field_id = model_field_obj.search(cr, uid, [('model_id', 'in', model_inherits), ('name', '=', field_split[0])], context=context)
                    if not field_id:
                        raise osv.except_osv(_('Error'), _('Field %s not found') % field_split[0])

                    cur_line['field_id'] = field_id[0]
                    field_br = model_field_obj.browse(cr, uid, field_id[0], context=context)
                    if len(field_split) == 2:
                        cur_line['relation'] = field_split[1]
                        # retrieve the real objet for the relation
                        relation_ids = self.pool.get('ir.model').search(cr, uid, [('model', '=', field_br.relation)], context=context)
                        if not relation_ids:
                            raise osv.except_osv(_('Error'), _('Model %s not found!') % field_br.relation)
                        cur_line['model_relation_id'] = relation_ids[0]

                    args['line_ids'].append((0, 0, cur_line))

                break

            implist_obj.write(cr, uid, [context.get('active_id')], args, context=context)

        except csv.Error, e:
            print 'csvError: %s' % str(e)
        except Exception, e:
            print 'Exception: %s' % str(e)
        finally:
            fpcsv.close()

        return {'type': 'ir.actions.act_window_close'}

ReadCsv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
