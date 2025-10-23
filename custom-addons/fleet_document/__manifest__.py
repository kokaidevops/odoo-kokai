{
    'name': 'Fleet Document',
    'version': '16.0.1',
    'summary': 'Fleet Document with Expiry Date',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Documents',
    'depends': [
        'document_expiry',
        'documents',
        'documents_fleet',
        'fleet',
    ],
    'data': [
        'views/document_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}