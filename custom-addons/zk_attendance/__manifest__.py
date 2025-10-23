{
    'name': 'Attendance from Fingerprint',
    'version': '16.0',
    'summary': 'Get Attendance from Fingerprint use pyzk library',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['hr', 'portal', 'report_xlsx', 'employee_attendance'],
    'data': [
        'security/ir.model.access.csv',

        'views/fingerprint_device_views.xml',
        'views/hr_employee_views.xml',

        'reports/report.xml',

        'wizards/device_extract_wizard_views.xml',
        'wizards/employee_attendance_wizard.xml',
        'wizards/employee_fingerprint_import_views.xml',
    ],
    'auto_install': False,
    'application': False,
}