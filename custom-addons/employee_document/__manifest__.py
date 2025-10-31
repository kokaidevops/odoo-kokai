{
    'name': 'Employee Document',
    'version': '16.0.1',
    'summary': 'Employee Document with Expiry',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'document_expiry',
        'documents',
        'documents_hr',
    ],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'auto_install': False,
    'application': False,
}