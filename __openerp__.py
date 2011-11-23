# -*- coding: utf-8 -*-
##############################################################################
#
#    document_csv module for OpenERP, module to import data from CSV source
#    Copyright (C) 2009-2011 SYLEAM (<http://www.Syleam.fr>)
#                  Christophe CHAUVET <christophe.chauvet@syleam.fr>
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

{
    'name': 'Import csv using document management',
    'version': '1.4.2',
    'category': 'Document',
    'description': """
    This module can import CSV file and easily than GTK Client
    """,
    'author': 'SYLEAM',
    'website': 'http://www.syleam.fr/',
    'images': [
        'images/syleam.png',
    ],
    'depends': [
        'document',
        'base_tools',
    ],
    'update_xml': [
        'security/ir.model.access.csv',
        'menu_view.xml',
        'format_data.xml',
        'directory_data.xml',
        'content_type_data.xml',
        'wizard/wizard.xml',
        'wizard/launch_view.xml',
        'wizard/read_csv_view.xml',
        'document_view.xml',
        #'export_view.xml',
    ],
    'demo_xml': [
        'demo/document.xml',
    ],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
