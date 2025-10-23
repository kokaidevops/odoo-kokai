{
    'name': 'Product Bundle',
    'version': '16.0.1',
    'summary': 'Product Bundle',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Product',
    'depends': [
        'product',
        'stock',
        'purchase',
        'purchase_request',
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/product_views.xml',
        'views/purchase_views.xml',
    ],
    'auto_install': False,
    'application': False,
}