{
    'name': 'Non Conforming Product',
    'version': '16.0',
    'summary': 'Non Conforming Product Report',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Non Conforming',
    'depends': [
        'qhse_program',
        'sequence_reset_period',
        'schedule_task',
        'department_detail',
        'company_director',
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/nonconforming_product_views.xml',
    ],
    'auto_install': False,
    'application': False,
}