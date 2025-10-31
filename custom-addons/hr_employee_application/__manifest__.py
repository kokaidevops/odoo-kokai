{
    'name': 'Kokai Employee Application',
    'version': '16.0.1',
    'summary': 'Form Employee Application adjust to requirement of PT. Kokai Indo Abadi',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Recruitment',
    'depends': [
        'hr_recruitment',
        'recruitment_request',
        'res_localization',
        'custom_payroll'
    ],
    'data': [
        'views/hr_applicant_views.xml'
    ],
    'auto_install': False,
    'application': False,
}