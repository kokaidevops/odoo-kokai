{
    'name': 'Employee Training',
    'version': '16.0',
    'description': '',
    'summary': 'Employee Training Program',
    'author': 'github.com/zdni',
    'website': '',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr',
        'approvals_portal',
        'approvals',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_evidence',
        'sequence_reset_period',
        'schedule_task'
    ],
    'data': [
        'data/approval_category_data.xml',
        'data/ir_sequence.xml',

        'security/ir.model.access.csv',

        'views/menu.xml',
        'views/annual_training_views.xml',
        'views/hr_training_views.xml',
        'views/training_configuration_views.xml',
        'views/res_users_views.xml',
    ],
    'auto_install': False,
    'application': False,
}