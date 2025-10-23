{
    'name': 'Todo List',
    'version': '16.0',
    'summary': 'Todo List for User Task',
    'author': 'github.com/zdni',
    'license': 'LGPL-3',
    'category': 'Tools',
    'depends': ['mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',

        'views/checklist_task_views.xml',
        'views/hr_department_views.xml',
    ],
    'auto_install': False,
    'application': False,
}