# -*- coding: utf-8 -*-
{
    'name': 'BigFour Cashbox Portal',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Portal for cashier operations - payments, collections, expenses, and transfers',
    'description': """
BigFour Cashbox Portal
======================

This module provides a portal interface for cashier operations including:

* Vendor bill payments
* Customer invoice collections  
* Cash expenses recording
* Uninvoiced revenue recording
* Cash transfers between cashboxes
* Receipt printing for all operations
* Approval workflow for all transactions

Features:
---------
* Portal user interface for cashiers
* Draft/Submit/Approve workflow
* Automatic journal entry creation
* Receipt printing with sequential numbers
* Multi-currency support
* Photo receipt upload
* Email notifications
* Comprehensive reporting

Compatibility:
--------------
* Odoo 18.0+
* Fully compatible with Odoo Community and Enterprise
    """,
    'author': 'BigFour',
    'website': 'https://www.bigfour.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'portal',
        'mail',
        'web',
    ],
    'data': [
        'security/cashbox_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/sequence_data.xml',
        'data/mail_templates.xml',
        'views/cashier_expense_views.xml',
        'views/cashbox_payment_views.xml',
        'views/cashbox_collection_views.xml',
        'views/cashbox_uninvoiced_views.xml',
        'views/cashbox_transfer_views.xml',
        'views/cashbox_portal_menu.xml',
        'views/portal_main_menu.xml',
        'views/portal_templates.xml',
        'reports/cashbox_receipt_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'bigfour_cashbox/static/src/css/portal.css',
            'bigfour_cashbox/static/src/js/portal.js',
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'images': ['static/description/icon.png'],
}

