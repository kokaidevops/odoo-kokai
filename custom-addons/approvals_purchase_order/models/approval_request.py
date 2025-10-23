from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')
]

class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_purchase_order = fields.Selection(CATEGORY_SELECTION, string='Has Purchase Request', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    has_purchase_order = fields.Selection(related='category_id.has_purchase_order')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_pr = self.env.company.approval_po_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.purchase_order_id.sudo().action_need_improvement(request.refused_reason)
                elif request.request_status == 'approved':
                    request.purchase_order_id.sudo().action_approved()
                elif request.request_status == 'cancel':
                    request.purchase_order_id.sudo().button_cancel()

        return res
