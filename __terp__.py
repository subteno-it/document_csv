# -*- coding: utf-8 -*-
##############################################################################
#
#    2ed_profile module for OpenERP, profile for 2ed customer
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Christophe CHAUVET
#
#    This file is a part of 2ed_profile
#
#    2ed_profile is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    2ed_profile is distributed in the hope that it will be useful,
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
    'version': '1.0',
    'category': 'Document',
    'description': """
    This module can import CSV file from the DMS
    - Put with FTP client in the directory
    - The import start automaticaly after full transfert
    """,
    'author': 'Syleam',
    'depends': [
        'document',
    ],
    'update_xml': [
        #'security/groups.xml',
        #'security/ir.model.access.csv',
        #'data/sequence.xml',
        #'view/menu.xml',
        #'wizard/wizard.xml',
        #'report/report.xml',
        'view/document.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
