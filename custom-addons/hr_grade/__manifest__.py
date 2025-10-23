{
    'name': 'Grade of Employee',
    'version': '16.0',
    'description': '',
    'summary': 'Set Grade for Employee and Job Position',
    'author': 'github.com/zdni',
    'website': '',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['hr', 'hr_contract', 'hr_payroll_configuration'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_grade_views.xml',
    ],
    'auto_install': False,
    'application': False,
}