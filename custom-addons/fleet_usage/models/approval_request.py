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

    has_fleet_usage = fields.Selection(CATEGORY_SELECTION, string='Has Fleet Usage', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    fleet_usage_id = fields.Many2one('fleet.usage', string='Fleet Usage')
    has_fleet_usage = fields.Selection(related='category_id.has_fleet_usage')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.company.approval_fleet_usage_id.id:
                if request.request_status == 'refused':
                    request.fleet_usage_id.sudo().action_refused(self.refused_reason)
                elif request.request_status == 'approved':
                    request.fleet_usage_id.sudo().action_approved()
        return res