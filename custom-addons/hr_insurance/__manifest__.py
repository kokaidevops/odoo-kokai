{
    'name': 'HR Insurance',
    'version': '16.0.1',
    'summary': "Module for Indonesian's Insurance, with BPJS TK and BPJS Kes",
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'custom_payroll',
        'hr_contract',
        'hr_payroll',
    ],
    'data': [
        'data/hr_insurance_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_salary_rule_data.xml',

        'security/ir.model.access.csv',

        'views/hr_insurance_views.xml',
    ],
    'auto_install': False,
    'application': False,
}