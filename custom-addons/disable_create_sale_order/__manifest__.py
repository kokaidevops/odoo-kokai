{
    'name': 'Disable Create SO',
    'version': '16.0',
    'summary': 'Disable button "Create" in Tree View on Sales Menu',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Sales',
    'depends': [
        'sale',
        'sale_management',
    ],
    'data': [
        'views/sale_order_views.xml'
    ],
    'auto_install': False,
    'application': False,
}