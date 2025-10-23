{
    'name': 'Approvals for Expense',
    'version': '16.0',
    'summary': 'Approval Request for Expense',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Expense',
    'depends': [
        'approvals_portal',
        'approvals',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_settings',
        'custom_activity',
        'department_detail',
        'hr_expense',
        'hr_expense_sequence',
        'approvals_evidence',
    ],
    'data': [
        'data/approval_category_data.xml',

        'views/approval_request_views.xml',
        'views/hr_expense_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}