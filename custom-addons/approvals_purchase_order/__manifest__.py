{
    'name': 'Approvals Purchase Order',
    'version': '16.0',
    'summary': 'Request Approval Purchase Order',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'approvals_evidence',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason', 
        'approvals_settings',
        'company_director', 
        'custom_activity',
        'department_detail',
        'kokai_purchase_order',
        'purchase', 
    ],
    'data': [
        'data/approval_category_data.xml',

        'views/approval_request_views.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}