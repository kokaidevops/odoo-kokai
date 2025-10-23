{
    'name': 'Religion',
    'version': '16.0.1',
    'summary': 'Module for Religion',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr'
    ],
    'data': [
        'data/hr_religion_data.xml',

        'security/ir.model.access.csv',

        'views/hr_religion_views.xml',
    ],
    'auto_install': False,
    'application': False,
}