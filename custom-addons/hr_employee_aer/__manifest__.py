{
    'name': 'HR Employee AER',
    'version': '16.0.1',
    'summary': 'Average Effective Rate for Employee',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr',
        'hr_contract',
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/hr_employee_aer_views.xml',
    ],
    'auto_install': False,
    'application': False,
}