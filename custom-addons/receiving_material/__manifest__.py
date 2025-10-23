{
    'name': 'Receiving of Material',
    'version': '16.0',
    'summary': 'Form Receiving Material use in PT. Kokai \n Additional Feature in Stock Picking for Checking Condition of Product Receiving',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Inventory',
    'depends': [
        'stock', 
        'schedule_task', 
        'custom_purchase_request', 
        'approvals',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_evidence',
    ],
    'data': [
        'data/data.xml',
        'views/stock_move_line_views.xml',
    ],
    'auto_install': False,
    'application': False,
}