{
    'name': 'OHS Inspection',
    'version': '16.0',
    'summary': 'OHS Inspection with Nonconformity Report',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Health and Safety',
    'depends': [
        'approvals_portal',
        'approvals',
        'approvals_position',
        'approvals_refused_reason',
        'qhse_program',
        'schedule_task',
        'approvals_evidence',
    ],
    'data': [
        'data/ir_sequence.xml',
        'data/data.xml',
        
        'security/ir.model.access.csv',

        'views/ohs_nonconformity_views.xml',
        'views/inspection_survey_views.xml',
    ],
    'auto_install': False,
    'application': False,
}