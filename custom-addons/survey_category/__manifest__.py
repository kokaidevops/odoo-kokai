{
    'name': 'Survey Category',
    'version': '16.0',
    'summary': 'Module setting for survey category list',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Survey',
    'depends': [ 'survey' ],
    'data': [
        'security/ir.model.access.csv',

        'views/survey_category_views.xml',
    ],
    'auto_install': False,
    'application': False,
}