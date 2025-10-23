{
    'name': 'Minutes of Meeting',
    'version': '16.0',
    'summary': 'Module Minutes of Meeting in Schedule',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Productivity',
    'depends': [
        'calendar',
        'custom_activity', 
        'department_detail', 
        'employee_attendance',
        'many2many_attachment_preview',
        'note',
    ],
    'data': [
        'data/data.xml',
        
        'security/ir.model.access.csv',

        'views/calendar_event_views.xml',
        'views/res_users_views.xml',
    ],
    'auto_install': False,
    'application': False,
}