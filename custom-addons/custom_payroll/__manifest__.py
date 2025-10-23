{
    'name': 'Extra Rule Payroll',
    'version': '16.0.1',
    'summary': 'Some Extra Rule for Payroll',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Payroll',
    'depends': [
        'custom_employee',
        'employee_attendance',
        'hr',
        'hr_contract',
        'hr_payroll',
        'hr_payroll_account',
        'hr_work_entry',
        'res_localization',
    ],
    'data': [
        'data/hr_minimum_wage_data.xml',
        'data/hr_allowance_data.xml',
        'data/hr_payroll_structure_type_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_salary_rule_data.xml',

        'security/ir.model.access.csv',

        'views/hr_payroll_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}