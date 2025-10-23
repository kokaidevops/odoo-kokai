{
    'name': 'Product Datasheet',
    'version': '16.0',
    'summary': 'Product Datasheet Form',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Product',
    'depends': [
        'mrp',
        'product_variant_configurator',
        'sale_management',
        'sequence_reset_period',
    ],
    'data': [
        'security/group_security.xml',
        'security/ir.model.access.csv',

        'views/product_datasheet_views.xml',
        'views/sale_order_views.xml',
    ],
    'auto_install': False,
    'application': False,
}