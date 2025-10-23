{
    'name': 'List of Documents',
    'version': '16.0',
    'summary': 'List of Documents',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Forms',
    'depends': [
        'approvals_portal',
        'approvals', 
        'approvals_position',
        'approvals_refused_reason',
        'approvals_settings',
        'custom_activity',
        'department_user', 
        'approvals_evidence',
        'qhse_program', 
        'sequence_reset_period',
    ],
    'data': [
        'data/data.xml',
        'data/ir_sequence.xml',

        'security/ir.model.access.csv',
        
        'views/amendment_document_views.xml',
        'views/list_of_documents_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'application': False,
}