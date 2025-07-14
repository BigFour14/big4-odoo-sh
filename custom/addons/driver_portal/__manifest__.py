{
    'name': 'Driver Portal',
    'version': '1.0',
    'summary': 'A portal for drivers to manage their trips, vehicles, and documents.',
    'author': 'Manus AI',
    'depends': ['base', 'fleet'],
    'data': [
        'security/driver_portal_security.xml',
        'security/ir.model.access.csv',
        'views/driver_trip_views.xml',
        'views/driver_document_views.xml',
        'views/driver_dashboard_views.xml',
        'reports/driver_trip_report.xml',
        'reports/expired_documents_report.xml',
        'data/driver_portal_data.xml',
        'data/driver_portal_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'driver_portal/static/src/css/driver_portal.css',
            'driver_portal/static/src/js/driver_portal.js',
        ],
    },
    'installable': True,
    'application': True,
}


