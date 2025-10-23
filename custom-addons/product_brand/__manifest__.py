{
    'name': 'Product Brand',
    'version': '16.0',
    'summary': """
        Module for Product Brand
        Product Brand have their own model
        Brand not assign to Variant or Product Template, but assign in SO Line, PR/PO Line, and Move Line
    """,
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Product',
    'depends': [
        'purchase',
        'purchase_request',
        'sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/product_brand_security.xml',

        'views/product_brand_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}