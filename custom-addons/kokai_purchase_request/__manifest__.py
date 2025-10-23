{
    'name': 'Kokai Purchase Request',
    'version': '16.0',
    'summary': 'This module add custom field for Purchase Request Document at PT. Kokai Indo Abadi',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Purchase',
    'depends': [
        'company_director',
        'custom_activity', 
        'department_detail', 
        'department_user', 
        'many2many_attachment_preview',
        'ps_binary_field_attachment_preview',
        'purchase_request', 
        'purchase_request_line_state',
    ],
    'data': [
        'data/data.xml',
        'data/purchase_request_type_data.xml',
        
        'security/ir.model.access.csv',

        'views/purchase_order_views.xml',
        'views/purchase_request_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}