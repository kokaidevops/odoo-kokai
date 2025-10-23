{
    'name': 'Fleet Usage',
    'version': '16.0',
    'summary': 'Form for Fleet Usage',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'approvals', 
        'approvals_settings',
        'custom_activity',
        'fleet', 
        'fleet_equipment',
        'helpdesk',
        'helpdesk_detail',
        'sequence_reset_period', 
        'stock',
    ],
    'data': [
        'data/approval_category_data.xml',
        'data/ir_sequence.xml',

        'security/fleet_usage_security.xml',
        'security/ir.model.access.csv',

        'views/fleet_usage_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/res_config_settings_views.xml',

        'wizards/fleet_checked_wizard_views.xml',
    ],
    'auto_install': False,
    'application': False,
}