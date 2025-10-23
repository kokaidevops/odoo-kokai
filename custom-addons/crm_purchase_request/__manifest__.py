{
    'name': 'CRM Purchase Request',
    'version': '16.0',
    'summary': 'Purchase Request from CRM Lead',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Purchase',
    'depends': [
        'crm_management',
        'custom_purchase_request',
    ],
    'data': [
        'views/sale_order_views.xml'
    ],
    'auto_install': False,
    'application': False,
}