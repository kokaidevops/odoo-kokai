{
    'name': 'Product Equipment',
    'version': '16.0.1',
    'summary': 'Generate equipment from product stock with Lot/Serial Number',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Product',
    'depends': [
        'maintenance',
        'product',
        'product_bundle_pack',
        'stock',
    ],
    'data': [
        'views/product_views.xml',
        'views/stock_views.xml',
        'views/maintenance_equipment_views.xml',
    ],
    'auto_install': False,
    'application': False,
}