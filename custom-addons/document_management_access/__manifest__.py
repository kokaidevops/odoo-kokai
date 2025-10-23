{
    'name': 'Document Management Access',
    'version': '16.0',
    'summary': 'Document Management Access with Department for Document Module',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Documents',
    'depends': ['documents', 'hr', 'department_user'],
    'data': [
        'security/security.xml',

        'views/document_views.xml',
    ],
    'auto_install': False,
    'application': False,
}