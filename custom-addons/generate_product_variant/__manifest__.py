{
    'name': 'Generate Product Variant',
    'version': '16.0',
    'summary': 'Generate Product Variant with all Attribute from Product Template',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Inventory',
    'depends': ['stock', 'product_variant_configurator'],
    'data': [
        'security/ir.model.access.csv',

        'views/product_template_views.xml',

        'wizards/generate_product_wizard_views.xml',
    ],
    'auto_install': False,
    'application': False,
}