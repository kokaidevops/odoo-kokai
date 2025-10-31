{
    'name': 'Custom Approver',
    'version': '16.0.1',
    'summary': 'Custom Option for Approver in Approval',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Approvals',
    'depends': [
        'approvals',
        'approvals_evidence',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_settings',
    ],
    'data': [
        'views/approval_request_views.xml'
    ],
    'auto_install': False,
    'application': False,
}