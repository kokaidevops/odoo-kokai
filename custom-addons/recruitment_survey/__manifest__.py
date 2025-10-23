{
    'name': 'Recruitment Survey',
    'version': '16.0.1',
    'summary': 'Survey for Recruitment and post it to Recruitment Profile',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr_recruitment',
        'survey_category',
    ],
    'data': [
        'data/survey_category_data.xml',

        'views/survey_user_input_views.xml',
    ],
    'auto_install': False,
    'application': False,
}