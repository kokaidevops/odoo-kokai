from odoo import _, api, fields, models


class DocumentsFolder(models.Model):
    _inherit = 'documents.folder'

    department_ids = fields.Many2many('hr.department', string='Write Departments', copy=True)
    read_department_ids = fields.Many2many('hr.department', 'documents_folder_read_departments', string='Read Departments', copy=True)

    @api.onchange('parent_folder_id')
    def _onchange_parent_folder_id(self):
        for record in self:
            if record.parent_folder_id:
                record.department_ids = record.parent_folder_id.department_ids
                record.read_department_ids = record.parent_folder_id.read_department_ids
            else:
                record.department_ids = []
                record.read_department_ids = []
