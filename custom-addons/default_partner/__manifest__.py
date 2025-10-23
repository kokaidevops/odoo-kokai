{
    'name': 'Default Partner',
    'version': '16.0',
    'summary': 'Partner for Initial Choice that will be Replaced Later and Server Action to Set Partner as Customer or Vendor',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Marketing',
    'depends': ['base'],
    'data': [
        'data/default_partner.xml',
        
        'views/res_partner_views.xml',
    ],
    'auto_install': False,
    'application': False,
}