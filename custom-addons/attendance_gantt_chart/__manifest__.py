{
    'name': 'Attendance Gantt Chart',
    'version': '16.0.1',
    'summary': 'View Gantt Chart for Attendance',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Attendances',
    'depends': [
        'hr_attendance',
        'attendance_view_calendar',
    ],
    'data': [
        'views/hr_attendance_views.xml'
    ],
    'auto_install': False,
    'application': False,
}