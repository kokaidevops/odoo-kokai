from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    revision_approval_ids = fields.One2many('approval.request', 'so_revision_id', string='Approval Revision')
    revision_approval_count = fields.Integer('Approval Count', compute='_compute_revision_approval_count')
    can_revision = fields.Boolean('Can Revision?', compute='_compute_can_revision')

    @api.depends('revision_approval_ids', 'revision_approval_ids.request_status')
    def _compute_can_revision(self):
        for record in self:
            if record.revision_approval_count == 0:
                record.can_revision = False
                return
            record.can_revision = record.revision_approval_ids[0].request_status == 'approved'

    @api.depends('revision_approval_ids')
    def _compute_revision_approval_count(self):
        for record in self:
            record.revision_approval_count = len(record.revision_approval_ids)

    def request_approval_revision(self):
        self.ensure_one()
        ctx = dict(default_order_id=self.id, active_ids=self.ids)
        return {
            'name': _('Request Revision'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'request.revision.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def _prepare_approval_request(self):
        res = super(SaleOrder, self)._prepare_approval_request()
        res['so_revision_id'] = False
        return res

    def _prepare_approval_revision(self, reason):
        self.ensure_one()
        category_pr = self.env.company.so_revision_approval_id
        vals = {
            'name': 'Request Revision for ' + self.name,
            'so_revision_id': self.id,
            'order_id': False,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request for Revision {self.name} [{self.customer_po_number}] \n{reason}"
        }
        return vals

    def generate_approval_revision(self, reason):
        self.ensure_one()
        vals = self._prepare_approval_revision(reason=reason)
        request = self.env['approval.request'].create(vals)
        request.action_confirm()

    def action_view_revision_approval_request(self):
        if len(self.revision_approval_ids) == 0:
            return
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        action['domain'] = [('id', 'in', self.revision_approval_ids.ids)]
        return action

    def action_revision_approved(self):
        _logger.warning("action_revision_approved")
        try: 
            self.with_context(disable_cancel_warning=True).action_cancel()
        except Exception as e:
            raise ValidationError(e)
        # TODO notification to user

    def action_revision_rejected(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('sale.model_sale_order').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.account_executive_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'just_one',
        })

