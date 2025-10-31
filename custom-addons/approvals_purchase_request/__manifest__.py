{
    'name': 'Approvals - Purchase Request',
    'version': '16.0',
    'description': """
        This module adds to the Purchase Request to generate 
        Approval from Purchase Request
    """,
    'author': 'https://github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'approvals_approver_custom',
        'approvals_evidence',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason', 
        'approvals_settings',
        'company_director', 
        'custom_activity',
        'department_detail',
        'kokai_purchase_request',
    ],
    'data': [
        'data/approval_category_data.xml',
        'data/server_action.xml',
        
        'views/approval_request_views.xml',
        'views/purchase_request_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}