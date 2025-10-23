{
    'name': 'HR Qualification',
    'version': '16.0',
    'summary': 'Configuration for Employee & Job Qualification',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [ 'hr' ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',

        'views/hr_qualification_views.xml',
    ],
    'auto_install': False,
    'application': False,
}