from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class KokaiRab(models.Model):
    _inherit = 'kokai.rab'

    approval_ids = fields.One2many('approval.request', 'budget_plan_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def action_view_approval_request(self):
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        action['domain'] = [('id', 'in', approvals.ids)]
        return action

    def action_submit(self):
        self.ensure_one()
        category_pr = self.env.company.approval_budget_plan_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'budget_plan_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for {self.name} from {self.user_id.name} \n {self.notes}"
        }
        self.sudo().write({ 'state': 'to approve' })
        request = self.env['approval.request'].create(vals)
        request.action_confirm()
        return super().action_submit()

    def action_approve(self):
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('ks_kokai.model_kokai_rab').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': 'Please process the following Budget Planning as soon as possible. Thank You!',
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        return super().action_approve()

    def action_reject(self, reason):
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('ks_kokai.model_kokai_rab').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        return super().action_reject()