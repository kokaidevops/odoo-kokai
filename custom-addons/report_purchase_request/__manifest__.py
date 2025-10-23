{
    'name': 'Report Purchase Request',
    'version': '16.0',
    'summary': 'This module for print Report Purchase Request for PT. Kokai Indo Abadi',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Report',
    'depends': [
        'approvals_purchase_request', 
        'kokai_purchase_request',
        'purchase_request', 
        'report_py3o', 
    ],
    'data': [
        'views/purchase_request_views.xml',
        'reports/purchase_request_report_template.xml',
        'reports/reports.xml',
    ],
    'auto_install': False,
    'application': False,
}