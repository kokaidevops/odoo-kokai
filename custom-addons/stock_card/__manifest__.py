{
    'name': 'Stock Card',
    'version': '16.0',
    'summary': 'Stock Card Product',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Inventory',
    'depends': ['stock', 'sequence_reset_period'],
    'data': [
        'data/ir_sequence.xml',

        'security/ir.model.access.csv',
        
        'views/product_product_views.xml',
        'views/stock_card_views.xml',
    ],
    'auto_install': False,
    'application': False,
}