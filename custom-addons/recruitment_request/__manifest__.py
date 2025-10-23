{
    'name': 'Recruitment Request',
    'version': '16.0',
    'summary': 'Recruitment Request by each Department',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'approvals',
        'approvals_evidence',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_settings',
        'custom_activity',
        'department_detail',
        'department_user', 
        'hr_qualifications',
        'hr_recruitment', 
        'hr_skills',
    ],
    'data': [
        'data/approval_category_data.xml',
        'data/ir_sequence.xml',

        'security/group_security.xml',
        'security/ir_rules.xml',

        'security/ir.model.access.csv',

        'views/recruitment_request_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}