from odoo import _, api, fields, models

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_business_trip = fields.Selection(CATEGORY_SELECTION, string='Has Business Trip', default='no')


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    has_business_trip = fields.Selection(related='category_id.has_business_trip')
    trip_id = fields.Many2one('crm.business.trip', string='Trip')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_pr = self.env.company.approval_business_trip_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.purchase_order_id.sudo().action_rejected(request.refused_reason)
                elif request.request_status == 'approved':
                    request.purchase_order_id.sudo().action_approved()
                elif request.request_status == 'cancel':
                    request.purchase_order_id.sudo().button_cancel()

        return res