from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    document_expiry_ids = fields.One2many('base.document', 'employee_id', string='Document')
    document_expiry_count = fields.Integer('Document Count', compute='_compute_document_expiry_count', store=True)

    @api.depends('document_expiry_ids')
    def _compute_document_expiry_count(self):
        for record in self:
            record.document_expiry_count = len(record.document_expiry_ids)

    def action_show_document_expiry(self):
        action = self.env.ref('document_expiry.base_document_action').sudo().read()[0]
        action['domain'] = [('id', 'in', self.document_expiry_ids.ids)]
        action['context'] = {
            'default_based_on': 'employee',
            'default_employee_id': self.id,
        }
        return action
