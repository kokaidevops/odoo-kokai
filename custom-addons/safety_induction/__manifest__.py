{
    'name': 'Safety Induction',
    'version': '16.0',
    'summary': 'Safety Induction',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'OHS',
    'depends': [
        'qhse_program',
        'approvals_portal',
        'approvals',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_evidence',
        'schedule_task'
    ],
    'data': [
        'data/data.xml',
        'data/ir_sequence.xml',

        'security/ir.model.access.csv',

        'views/induction_topic_views.xml',
        'views/safety_induction_views.xml',
    ],
    'auto_install': False,
    'application': False,
}