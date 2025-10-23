{
    'name': 'Res Localization',
    'version': '16.0',
    'summary': 'Module for add Address Detail',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Localization',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        
        # 'data/res.city.csv',
        # 'data/res.subdistrict.csv',
        # 'data/res.ward.csv',

        'views/menu.xml',
        'views/res_city_views.xml',
        'views/res_subdistrict_views.xml',
        'views/res_ward_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
    ],
    'auto_install': False,
    'application': False,
}