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

    has_training_note = fields.Selection(CATEGORY_SELECTION, string='Has Training Note', default='no')

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    training_note_id = fields.Many2one('training.note', string='Training Note')
    has_training_note = fields.Selection(related='category_id.has_training_note')

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_request_status(self):
        res = super(ApprovalRequest, self)._compute_request_status()
        for request in self:
            if request.category_id.id == self.env.ref('training_note.approval_category_data_training_note').id:
                if request.request_status == 'refused':
                    request.training_note_id.sudo().action_refused()
                elif request.request_status == 'approved':
                    request.training_note_id.sudo().action_approved()
        return res