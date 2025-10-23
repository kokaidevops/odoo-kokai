{
    'name': 'Sales Achievement',
    'version': '16.0.1',
    'summary': 'Set salesperson target and record for achievement',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Sales',
    'depends': [
        'sale_management',
        'department_detail',
    ],
    'data': [
        'security/group_security.xml',
        'security/ir_rules.xml',
        'security/ir.model.access.csv',

        'views/sales_achievement_views.xml',
    ],
    'auto_install': False,
    'application': False,
}