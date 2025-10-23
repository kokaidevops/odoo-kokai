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

    has_annual_training = fields.Selection(CATEGORY_SELECTION, string='Has Annual Training', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    annual_training_id = fields.Many2one('annual.training', string='Annual Training')
    has_annual_training = fields.Selection(related='category_id.has_annual_training')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.ref('hr_training.approval_category_data_annual_training').id:
                if request.request_status == 'refused':
                    request.annual_training_id.sudo().action_need_improvement()
                elif request.request_status == 'approved':
                    request.annual_training_id.sudo().action_approved()
        return res