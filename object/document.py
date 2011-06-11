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
from tools import ustr
from tools import email_send as email
from tools import config
import time
import base64
import csv
import pooler
import logging

_logger = logging.getLogger('document_csv')

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


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
    }

    _defaults = {
        'ctx': lambda *a: '{}',
        'disable': lambda *a: True,
        'csv_sep': lambda *a: ';',
        'csv_esc': lambda *a: '"',
        'backup_filename': lambda *a: 'sample-%Y%m%d_%H%M%S.csv',
        'reject_filename': lambda *a: 'sample-%Y%m%d_%H%M%S.rej',
        'log_filename': lambda *a: 'sample-%Y%m%d_%H%M%S.log',
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
        'field_id': fields.many2one('ir.model.fields', 'Field', required=True),
        'relation': fields.selection([('id', 'ID'), ('db_id', 'DB ID'), ('search', 'Search')], 'Field relation', help='Search use name_search to match the record'),
        'create': fields.boolean('Create entry', help="If check, if entry doesn't exist, it must be created"),
        'refkey': fields.boolean('Reference Key', help='If check, this key is equal to ID in manual import'),
    }

import_list_line()


class ir_attachment(osv.osv):
    """Inherit this class to made the CSV treatment"""
    _inherit = 'ir.attachment'

    def import_csv(self, cr, uid, format_id, content, email_to, context):
        _logger.info('Start new CSV import')

        # launch process as multithread
        self.on_execute(cr, uid, cr.dbname, format_id, StringIO(base64.decodestring(content)), email_to, context)

        _logger.info('Launch import as thread')
        return True

    def on_execute(self, cr, uid, dbname, format_id, cfp, email_to, context=None):
        if context is None:
            context = {}

        #print 'content: %s' % cfp.getvalue()

        cr = pooler.get_db(dbname).cursor()

        # the file are store successfully, we can
        # for each file import, check if there insert in
        # import directory
        model_obj = self.pool.get('ir.model')
        field_obj = self.pool.get('ir.model.fields')
        import_obj = self.pool.get('document.import.list')
        line_obj = self.pool.get('document.import.list.line')

        _logger.info('module document_csv: begin import new file '.ljust(80, '*'))
        imp_data = import_obj.browse(cr, uid, format_id, context=context)
        context.update(eval(imp_data.ctx))

        logfp = StringIO()

        def log_compose(message):
            logfp.write(time.strftime('[%Y-%m-%d %H:%M:%S] '))
            logfp.write(message + '\n')
            return message

        #model = imp_data.model_id.model

        # Read all field name in the list
        uniq_key = False
        fld = []
        for l in imp_data.line_ids:
            args = {
                'name': l.name,
                'field': l.field_id.name,
                'type': l.field_id.ttype,
                'relation': l.field_id.relation,
                'key': l.refkey,
                'ref': l.relation,
            }
            fld.append(args)
            if l.refkey:
                uniq_key = l.name

        # Compose the header
        header = []
        rej_header = []
        if uniq_key:
            header.append(u'id')
        for h in fld:
            rej_header.append(h['name'])
            if h['type'] not in ('many2one', 'one2many', 'many2many'):
                header.append(h['field'])
            else:
                if h['ref'] in ('id', 'db_id'):
                    header.append('%s:%s' % (h['field'], h['ref']))
                else:
                    header.append(h['field'])

        _logger.debug('module document_csv: ' + log_compose('Object: %s' % imp_data.model_id.model))
        _logger.debug('module document_csv: ' + log_compose('Context: %r' % context))
        _logger.debug('module document_csv: ' + log_compose('Columns header original : %s' % ', '.join(rej_header)))
        _logger.debug('module document_csv: ' + log_compose('Columns header translate: %s' % ', '.join(header)))
        _logger.debug('module document_csv: ' + log_compose('Unique key (XML id): %r' % uniq_key))

        # Compose the line from the csv import
        lines = []
        rej_lines = []

        sep = chr(ord(imp_data.csv_sep[0]))
        _logger.debug('module document_csv: ' + log_compose('Separator: %s ' % imp_data.csv_sep))

        esc = None
        if imp_data.csv_esc:
            esc = chr(ord(imp_data.csv_esc[0]))
            _logger.debug('module document_csv: ' + log_compose('Escape: %s ' % imp_data.csv_esc))

        integ = True
        try:
            csvfile = csv.DictReader(cfp, delimiter=sep, quotechar=esc)
            for c in csvfile:
                tmpline = []
                rejline = []
                if uniq_key:
                    tmpline.append('%s_%s' % (imp_data.model_id.model.replace('.', '_'), str(c[uniq_key])))
                for f in fld:
                    fld_name = c[f['name']]
                    if f['type'] in ('many2one', 'one2many', 'many2many'):
                        if not c[f['name']].find('.') > 0:
                            if f['ref'] == 'id':
                                fld_name = '%s_%s' % (f['relation'].replace('.', '_'), c[f['name']])
                    tmpline.append(fld_name)
                    rejline.append(c[f['name']])
                _logger.debug('module document_csv: line: %r' % tmpline)
                lines.append(tmpline)
                rej_lines.append(rejline)
        except csv.Error, e:
            _logger.info('module document_csv: ' + log_compose('csv.Error: %r' % e))
            error = 'csv Error, %r' % e
            integ = False
        except KeyError, k:
            _logger.info('module document_csv: ' + log_compose('%r' % k))
            error = 'KeyError, %r' % k
            integ = False
        except UnicodeError:
            _logger.info('module document_csv: ' + log_compose('Unicode error, convert your file in UTF-8, and retry'))
            error = 'Unicode error, convert your file in UTF-8, and retry'
            integ = False
        except Exception, e:
            _logger.info('module document_csv: ' + log_compose('Error not defined ! : %r' % e))
            error = 'Error not defined'
            integ = False
        finally:
            # After treatment, close th StringIO
            cfp.close()

        if integ:
            _logger.debug('module document_csv: ' + log_compose('start import'))
            # Use new cusrsor to integrate the data, because if failed the backup cannot be perform
            cr_imp = pooler.get_db(cr.dbname).cursor()
            current_model = self.pool.get(imp_data.model_id.model)
            try:
                if imp_data.err_reject:
                    _logger.debug('module document_csv: ' + log_compose('Global mode'))
                    res = current_model.import_data(cr_imp, uid, header, lines, 'init', '', False, context=context)
                    if res[0] >= 0:
                        _logger.debug('module document_csv: ' + log_compose('%d line(s) imported !' % res[0]))
                        cr_imp.commit()
                    else:
                        cr_imp.rollback()
                        d = ''
                        for key, val in res[1].items():
                            d += ('\t%s: %s\n' % (str(key), str(val)))
                        error = 'Error trying to import this record:\n%s\nError Message:\n%s\n\n%s' % (d, res[2], res[3])
                        _logger.error('module document_csv: ' + log_compose('%r' % ustr(error)))

                    if current_model._parent_store:
                        _logger.debug('module document_csv: ' + log_compose('Compute the parent_store'))
                        current_model._parent_store_compute(cr)
                else:
                    rejfp = StringIO()
                    count_success = 0
                    count_errors = 0
                    _logger.debug('module document_csv: ' + log_compose('Unit mode'))
                    rej_file = csv.writer(rejfp, delimiter=sep, quotechar=esc, quoting=csv.QUOTE_NONNUMERIC)
                    rej_file.writerow(rej_header)

                    cpt_lines = 0
                    for li in lines:
                        _logger.debug('module document_csv: Import line %d' % (cpt_lines + 1))
                        try:
                            res = current_model.import_data(cr_imp, uid, header, [li], 'init', '', False, context=context)
                        except Exception, e:
                            res = [-1, {}, e.message, '']

                        if res[0] >= 0:
                            count_success += 1
                            cr_imp.commit()
                        else:
                            count_errors += 1
                            cr_imp.rollback()
                            log_compose(4 * '*')
                            log_compose('Error line %d: %s' % (cpt_lines + 2, ', '.join(rej_lines[cpt_lines])))
                            log_compose('Error message: %s' % res[2])
                            rej_file.writerow(rej_lines[cpt_lines])
                        cpt_lines += 1

                    log_compose(4 * '*')
                    _logger.debug('module document_csv: ' + log_compose('%d line(s) imported !' % count_success))
                    _logger.debug('module document_csv: ' + log_compose('%d line(s) rejected !' % count_errors))
                    if current_model._parent_store:
                        _logger.debug('module document_csv: ' + log_compose('Compute the parent_store'))
                        current_model._parent_store_compute(cr)

                    if count_errors:
                        rej_name = time.strftime(imp_data.reject_filename)
                        rej_enc = base64.encodestring(rejfp.getvalue())
                        rejfp.close()
                        rej_args = {
                            'name': rej_name,
                            'datas_fname': rej_name,
                            'parent_id': imp_data.reject_dir_id.id,
                            'datas': rej_enc,
                        }
                        if not self.create(cr, uid, rej_args):
                            _logger.error('module document_csv: impossible to create the reject file!')

            except Exception, e:
                cr_imp.rollback()
                error = e.message
                _logger.error(log_compose(e.message))
            finally:
                cr_imp.close()

            _logger.debug('module document_csv: ' + log_compose('end import'))
        else:
            _logger.info('module document_csv: ' + log_compose('import canceled, correct these errors and retry'))

        try:
            if imp_data.backup:
                # TODO backup this file, only in memory for now
                bck_file = time.strftime(imp_data.backup_filename)
                #self.write(cr, uid, ids, {'name': bck_file, 'datas_fname':bck_file, 'parent_id': imp_data.backup_dir_id.id}, context=context)
                _logger.debug('module document_csv: ' + log_compose('backup file: %s ' % bck_file))
            else:
                _logger.debug('module document_csv: ' + log_compose('file deleted !'))
        except Exception, e:
            _logger.info('module document_csv: ' + log_compose('Error when backup database ! : %r' % e))

        ## save the log file
        log_name = time.strftime(imp_data.log_filename)
        log_enc = base64.encodestring(logfp.getvalue())
        logfp.close()
        log_args = {
            'name': log_name,
            'datas_fname': log_name,
            'parent_id': imp_data.log_dir_id.id,
            'datas': log_enc,
        }
        if not self.create(cr, uid, log_args):
            _logger.error('module document_csv: impossible to create the log file!')

        if imp_data.err_mail:
            email_from = imp_data.mail_from
            if not email_from:
                email_from = config['email_from']
            legend = {}
            if not isinstance(res, bool) and res[0] >= 0:
                legend['count'] = res[0]
                email_to = imp_data.mail_cc
                subject = imp_data.mail_subject % legend
                body = imp_data.mail_body % legend
            else:
                email_to = imp_data.mail_cc_err
                subject = imp_data.mail_subject_err % legend
                body = imp_data.mail_body_err % {'error': error}

            if email_from and email_to:
                email(email_from, email_to, subject, body)
                _logger.debug('module document_csv: Sending mail [OK]')
            else:
                _logger.warning('module document_csv: Sending mail [FAIL]')

        # Add trace on the log, when file was integrate
        _logger.debug('module document_csv: end import new file '.ljust(80, '*'))

        cr.commit()
        cr.close()
        return True

ir_attachment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
