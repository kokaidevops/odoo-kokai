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

    has_amendment_document = fields.Selection(CATEGORY_SELECTION, string='Has Amendment Document', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    amendment_document_id = fields.Many2one('amendment.document', string='Amendment Document')
    has_amendment_document = fields.Selection(related='category_id.has_amendment_document')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.company.approval_amendment_id.id:
                if request.request_status == 'refused':
                    request.amendment_document_id.sudo().action_need_improvement(self.refused_reason)
                elif request.request_status == 'approved':
                    request.amendment_document_id.sudo().action_approved()
        return res