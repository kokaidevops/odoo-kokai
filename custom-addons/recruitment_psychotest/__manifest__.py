{
    'name': 'Recruitment Psychological Test',
    'version': '16.0.1',
    'summary': 'Psychological Test in Recruitment Process',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr_recruitment', 
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/hr_applicant_views.xml',
        'views/recruitment_test_views.xml',
    ],
    'auto_install': False,
    'application': False,
}