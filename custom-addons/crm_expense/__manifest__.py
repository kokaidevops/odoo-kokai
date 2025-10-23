{
    'name': 'CRM Expense',
    'version': '16.0',
    'summary': 'Related CRM and Expense',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Expense',
    'depends': [
        'crm_management',
        'hr_expense',
    ],
    'data': [
        'views/hr_expense_views.xml'
    ],
    'auto_install': False,
    'application': False,
}