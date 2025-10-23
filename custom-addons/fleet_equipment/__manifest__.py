{
    'name': 'Fleet Equipment',
    'version': '16.0',
    'summary': 'Default Equipment for Fleet',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Vehicle',
    'depends': [
        'fleet', 'stock'
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/fleet_vehicle_views.xml',
    ],
    'auto_install': False,
    'application': False,
}