# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HR&Sales timesheet extension',
    'version': '1.0',
    'category': 'Services/Timesheets',
    'sequence': 200,
    'summary': 'Timesheet extention',
    'author': 'Helvethink',
    'description': """
This module completes the hr_timesheet module.
==========================================

It offers detailed timesheets, with task name, invoice date, due date, the payment status and ref.
    """,
    'depends': ['hr_timesheet','sale_timesheet'],
    'installable': True,
    'data': [
        'security/ir.model.access.csv',
        'report/timesheet_analysis_report_view.xml',
    ],
    'images': ['static/description/icon.png'],
    'license': 'Other OSI approved licence'
}
