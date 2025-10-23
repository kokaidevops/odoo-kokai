{
    'name': 'Report Expense',
    'version': '16.0',
    'summary': 'Report Expense py3o',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Tools',
    'depends': ['hr_expense', 'report_py3o',],
    'data': [
        'reports/reports.xml',
        'views/hr_expense_views.xml',
    ],
    'auto_install': False,
    'application': False,
}