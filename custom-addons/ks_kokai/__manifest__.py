{
    'name': "ks_kokai",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': [
        'auto_generate_lot_number',
        'base',
        'crm_management',
        'mrp', 
        'mrp_account',
        'product',
        'purchase_request',
        'stock', 
    ],

    'data': [
        'data/kokai_rab_category.xml',
        'data/bmo_sequence.xml',
        'security/ir.model.access.csv',
        'security/rab_security.xml',
        # 'security/product_category_template_security.xml',
        'views/crm_lead_views.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/stock_lot_views.xml',
        'views/product_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/kokai_rab_dashboard.xml',
        'views/kokai_rab_views.xml',
        # 'wizards/generate_product_wizard_views.xml',
        'views/batch_mo_views.xml',
        'views/product_category_template_views.xml',
        'wizards/stock_location_wizard.xml',
        'wizards/product_variant_wizard_view.xml',
        'views/account_budget_pnl_views.xml',
        'wizards/import_1_to_many_views.xml',        
        # 'wizards/generate_mo_wizard.xml',
        # 'views/bmo.xml'
        # 'wizards/product_template_wizard.xml'
        # 'views/stock_move_views.xml',        
    ],
}
