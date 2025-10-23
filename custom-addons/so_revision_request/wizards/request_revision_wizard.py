from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RequestRevisionWizard(models.TransientModel):
    _name = 'request.revision.wizard'
    _description = 'Request Revision Wizard'

    order_id = fields.Many2one('sale.order', string='Order')
    reason = fields.Html('Reason')

    def action_confirm(self):
        self.ensure_one()
        if not self.order_id:
            raise ValidationError("Sale Order not Found")
        self.order_id.generate_approval_revision(self.reason)