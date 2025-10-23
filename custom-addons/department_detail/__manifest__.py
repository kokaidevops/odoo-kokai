{
    'name': 'Department Detail',
    'version': '16.0',
    'summary': 'Department Detail, include Team, Detail and Etc.',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['hr', 'sequence_reset_period', 'department_user', 'stock', 'project'],
    'data': [
        'data/data.xml',
        'data/work_area_category_data.xml',

        'security/group_security.xml',
        'security/group_security_work_area.xml',
        'security/ir.model.access.csv',

        'views/hr_department_views.xml',
        'views/hr_work_area_views.xml',

        'wizards/generate_sequence_wizard.xml',
    ],
    'auto_install': False,
    'application': False,
}