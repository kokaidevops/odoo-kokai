{
    'name': 'Kokai Purchase Order',
    'version': '16.0.1',
    'summary': 'Custom Purchase Order for PT. Kokai Indo Abadi',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Purchase',
    'depends': [
        'confirmation_wizard',
        'default_partner',
        'purchase',
        'purchase_request',
        'sequence_reset_period',
    ],
    'data': [
        'data/data.xml',
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',

        'views/purchase_views.xml',

        'wizard/purchase_request_line_make_purchase_order_view.xml',
    ],
    'auto_install': False,
    'application': False,
}