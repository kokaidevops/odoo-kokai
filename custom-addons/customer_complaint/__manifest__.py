{
    'name': 'Customer Complaint',
    'version': '16.0',
    'summary': 'Customer Complaint Form',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Service',
    'depends': [
        'company_director',
        'department_detail',
        'hr',
        'list_of_documents',
        'qhse_program',
        'schedule_task',
        'sequence_reset_period',
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/customer_complaint_views.xml',
    ],
    'auto_install': False,
    'application': False,
}