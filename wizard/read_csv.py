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
        print 'active_id: %s' % context.get('active_id', 0)
        implist_obj = self.pool.get('document.import.list')
        implist = implist_obj.browse(cr, uid, context.get('active_id'), context=context)
        cur = self.browse(cr, uid, ids[0], context=context)
        fpcsv = StringIO(base64.decodestring(cur.import_file))
        fpcsv.seek(0)

        sep = chr(ord(implist.csv_sep[0]))
        esc = implist.csv_sep and chr(ord(implist.csv_esc[0])) or None

        try:
            csvfile = csv.reader(base64.decodestring(cur.import_file).splitlines(), delimiter=sep, quotechar=esc)
            res = []
            for c in csvfile:
                args = {'line_ids': [(0, 0, {'name': x}) for x in c]}
                break

            print args
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
