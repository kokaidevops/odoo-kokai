{
    'name': 'Report Payslip',
    'version': '16.0.1',
    'summary': 'This module for print Salary Slip and Report Payslip Batch in PT. Kokai Indo Abadi',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Report',
    'depends': [
        'custom_payroll',
        'report_py3o',
    ],
    'data': [
        'security/ir.model.access.csv',

        'reports/reports.xml',
        'views/hr_payslip_views.xml',
        'wizards/generate_report_payslip_wizard_views.xml',
    ],
    'auto_install': False,
    'application': False,
}