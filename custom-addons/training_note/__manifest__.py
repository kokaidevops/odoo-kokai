{
    'name': 'Employee Training Note',
    'version': '16.0',
    'summary': 'Employee Training Note about Result',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['hr_training', 'many2many_attachment_preview'],
    'data': [
        'data/approval_category_data.xml',
        'data/ir_sequence.xml',

        'security/ir.model.access.csv',

        'views/hr_training_views.xml',
        'views/training_note_views.xml',
    ],
    'auto_install': False,
    'application': False,
}