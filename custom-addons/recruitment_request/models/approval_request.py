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

    has_recruitment_request = fields.Selection(CATEGORY_SELECTION, string='Has Recruitment Request', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    recruitment_request_id = fields.Many2one('recruitment.request', string='Recruitment Request')
    has_recruitment_request = fields.Selection(related='category_id.has_recruitment_request')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.company.recruitment_request_approval_id.id:
                if request.request_status == 'refused':
                    request.recruitment_request_id.sudo().action_refused(request.refused_reason)
                elif request.request_status == 'approved':
                    request.recruitment_request_id.sudo().action_approved()
        return res