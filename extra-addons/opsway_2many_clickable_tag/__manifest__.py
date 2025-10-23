# -*- coding: utf-8 -*-
{
    'name': 'One2Many & Many2Many Clickable Tag Widget',
    'version': '16.0.0.2.0',
    'category': 'Tools',
    'summary': 'Allow clicking many2many_tag to open related record\'s form in one click.',
    'description': 'Click on a tag in a list or form -> associated record\'s form will open.\n'
                   'Press Shift + Click -> you will get original tags color picker.\n'
                   'In a list view, tags are only clickable if the list view is editable or if a line is in edit mode '
                   'when the list has a multi_edit option.',
    'author': 'Opsway',
    'website': 'https://opsway.com',
    'depends': ['web'],
    'images': ['static/description/banner.png'],
    'assets': {
        'web.assets_backend': [
            'opsway_2many_clickable_tag/static/src/js/many_tags_clickable.js',
            'opsway_2many_clickable_tag/static/src/js/tags_list.js',
            'opsway_2many_clickable_tag/static/src/js/tags_list.xml',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
