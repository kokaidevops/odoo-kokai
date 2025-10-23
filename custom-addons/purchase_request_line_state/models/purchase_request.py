from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    def button_draft(self):
        res = super().button_draft()
        self.mapped('line_ids').action_draft()
        return res

    def button_to_approve(self):
        res = super().button_to_approve()
        self.mapped('line_ids').filtered(lambda line: line.request_state == 'draft').action_to_approve()
        return res

    def button_approved(self):
        res = super().button_approved()
        self.mapped('line_ids').filtered(lambda line: line.request_state != 'rejected').action_to_approve()
        return res

    def button_rejected(self):
        res = super().button_rejected()
        self.mapped('line_ids').action_rejected()
        return res

class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    def action_draft(self):
        self.write({'request_state': 'draft'})

    def action_to_approve(self):
        self.write({'request_state': 'to_approve'})

    def action_approved(self):
        self.write({'request_state': 'approved'})

    def action_rejected(self):
        for record in self:
            if record.request_state not in ['draft', 'to_approve', 'rejected']:
                raise ValidationError("Can't reject Line not in Draft or To be Approved state")
            record.write({'request_state': 'rejected'})

    request_state = fields.Selection([
        ("draft", "Draft"),
        ("to_approve", "To be approved"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], string='Request State', default='draft', related='')