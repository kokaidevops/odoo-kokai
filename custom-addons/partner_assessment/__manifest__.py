{
    'name': 'Partner Assessment',
    'version': '16.0',
    'summary': 'Survey Assessment for Partner',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Contact',
    'depends': [
        'approvals',
        'approvals_evidence',
        'approvals_portal',
        'approvals_position',
        'approvals_refused_reason',
        'approvals_settings',
        'contacts',
        'stock',
        'survey',
        'survey_category',
    ],
    'data': [
        'data/partner_assessment_point_data.xml',
        'data/survey_category_data.xml',

        'security/ir.model.access.csv',

        'views/assessment_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
    ],
    'auto_install': False,
    'application': False,
}