{
    'name': 'SO Versioning',
    'version': '16.0.1',
    'summary': 'Request Revision for SO from Salesperson',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Sale Management',
    'depends': [
        'approvals',
        'approvals_evidence',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_settings',
        'crm_management',
        'sale_order_revision',
    ],
    'data': [
        'data/approval_category_data.xml',

        'security/ir.model.access.csv',

        'views/approval_request_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',

        'wizards/request_revision_wizard_views.xml',
    ],
    'auto_install': False,
    'application': False,
}