{
    'name': ' Sequence Expense',
    'version': '16.0',
    'summary': 'Sequence for Expense Request',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Expenses',
    'depends': [
        'hr_expense',
        'sequence_reset_period',
    ],
    'data': [
        'data/ir_sequence.xml',

        'views/hr_expense_sheet_views.xml',
    ],
    'auto_install': False,
    'application': False,
}