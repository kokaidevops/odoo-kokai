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

    has_purchase_request = fields.Selection(CATEGORY_SELECTION, string='Has Purchase Request', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request')
    has_purchase_request = fields.Selection(related='category_id.has_purchase_request')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        
        for request in self:
            category_pr = self.env.company.approval_pr_id
            if request.category_id.id == category_pr.id:
                if request.request_status == 'refused':
                    request.purchase_request_id.sudo().action_need_improvement(self.refused_reason)
                elif request.request_status == 'approved':
                    request.purchase_request_id.sudo().action_approved()

        return res