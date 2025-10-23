{
    'name': 'Job Position Level',
    'version': '16.0.1',
    'summary': 'Module for Setting Employee Level in Job Position',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'department_detail',
        'hr',
        'hr_contract',
    ],
    'data': [
        'data/data.xml',

        'security/ir.model.access.csv',

        'views/hr_job_level_views.xml',
    ],
    'auto_install': False,
    'application': False,
}