{
    'name': 'Custom Maintenance',
    'version': '16.0.1',
    'summary': 'Custom Maintenance',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Maintenance',
    'depends': [
        'helpdesk',
        'maintenance',
    ],
    'data': [
        'data/data.xml',
        'data/helpdesk_team_data.xml',

        'views/helpdesk_views.xml'
    ],
    'auto_install': False,
    'application': False,
}