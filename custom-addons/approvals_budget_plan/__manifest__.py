{
    'name': 'Approvals Budget Plan',
    'version': '16.0.1',
    'summary': 'Module Approval for Budget Plan',
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
        'ks_kokai',
    ],
    'data': [
        'data/approval_category_data.xml',

        'views/rab_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}