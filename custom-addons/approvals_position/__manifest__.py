{
    'name': 'Approvals Position',
    'version': '16.0',
    'summary': 'This module add position of Approver in Approval Request',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['approvals', 'portal'],
    'data': [
        'data/position_approver_data.xml',
        
        'security/ir.model.access.csv',
        
        'views/approval_category_approver_views.xml',
        'views/position_approver_views.xml',
        'views/approval_request_views.xml',
    ],
    'auto_install': False,
    'application': False,
}