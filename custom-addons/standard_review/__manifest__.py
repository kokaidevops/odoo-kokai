{
    'name': 'Standard Review',
    'version': '16.0',
    'summary': 'Standard Review',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Technical',
    'depends': ['qhse_program', 'sequence_reset_period'],
    'data': [
        'data/ir_sequence.xml',

        'security/ir.model.access.csv',

        'views/standard_review_views.xml',
    ],
    'auto_install': False,
    'application': False,
}