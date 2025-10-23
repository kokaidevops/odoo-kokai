{
    'name': 'Approvals Refused Reason',
    'version': '16.0.0',
    'summary': 'This module add reason to approval request when approver refused the request',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['approvals'],
    'data': [
        'security/ir.model.access.csv',
        
        'views/approval_request_views.xml',
        'wizards/approval_refused_reason_wizard.xml',
    ],
    'auto_install': False,
    'application': False,
}