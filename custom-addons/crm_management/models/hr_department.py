from odoo import _, api, fields, models

class HRDepartment(models.Model):
    _inherit = 'hr.department'

    include_in_crm = fields.Boolean('Include In CRM?', default=True)