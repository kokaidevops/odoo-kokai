{
    'name': 'CRM Business Trip',
    'version': '16.0.1',
    'summary': 'Module for Business Trip from CRM Lead',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Sales',
    'depends': [
        'approvals',
        'approvals_evidence',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_settings',
        'crm',
        'crm_management',
        'custom_activity',
        'minutes_of_meeting',
        'res_localization',
    ],
    'data': [
        'data/ir_sequence.xml',

        'security/ir.model.access.csv',

        'views/crm_business_trip_views.xml',
        'views/crm_lead_views.xml',
        # 'views/res_partner_views.xml',
    ],
    'auto_install': False,
    'application': False,
}