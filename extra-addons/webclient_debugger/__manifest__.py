# -*- coding: utf-8 -*-
{
    "name": "Debugger",
    "summary": """
        Adding a debug mode toggler to Navbar of odoo webclient.
        Debug, Inspectorl, Fix, Trace, debugger, debug, analyze, debugpro, tracetool, fixer, devtools, debugaid, """,
    "description": """
        Adding a debug mode toggler to Navbar of odoo webclient.
        Debug, Inspectorl, Fix, Trace, debugger, debug, analyze, debugpro, tracetool, fixer, devtools, debugaid, """,
    "version": "16.0.1.0.1",
    "license": "LGPL-3",
    "author": "Nazir Khan Wazir",
    "website": "https://github.com/Nazirkhanwazir/My-Odoo-Store-Apps/tree/16.0/webclient_debugger",
    "depends": ["web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            'webclient_debugger/static/src/js/debug_menu/*',
            'webclient_debugger/static/src/css/*',
        ],
    },
    "installable": True,
    'images': ['static/description/banner.gif'],
}
