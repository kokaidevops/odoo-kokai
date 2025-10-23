{
    'name': 'Product QR Code',
    'version': '16.0',
    'summary': 'Generate Product QR Code for Lots/Serial Number',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Inventory',
    'depends': ['stock', 'sequence_reset_period'],
    'data': [
        'data/ir_sequence.xml',
        'views/product_template_views.xml'
    ],
    'auto_install': False,
    'application': False,
}