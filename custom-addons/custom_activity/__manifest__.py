{
    'name': 'Customization Activity',
    'version': '16.0',
    'summary': 'Custom activity module for notification, timesheet and other',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Tools',
    'depends': [
        'timesheet_grid',
        'mail',
        'sale_timesheet_enterprise',
        'sequence_reset_period',
    ],
    'data': [
        'data/mail_activity_data.xml',

        'views/hr_timesheet_views.xml',
        'views/mail_activity_type_views.xml',
        'views/mail_activity_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}