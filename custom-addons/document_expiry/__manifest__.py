{
    'name': 'Document with Expiry',
    'version': '16.0.1',
    'summary': 'Document with Expiry',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Documents',
    'depends': [
        'activity_planning',
        'base',
        'custom_activity',
        'documents',
        'mail',
        'hr_expense',
    ],
    'data': [
        'data/data.xml',

        'security/ir.model.access.csv',

        'views/document_views.xml',
        'views/hr_expense_sheet.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}