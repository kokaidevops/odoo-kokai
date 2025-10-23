from odoo import _, api, fields, models, Command, _
from odoo.exceptions import UserError
from odoo.tools import email_split, float_is_zero, float_repr, float_compare, is_html_empty
from odoo.tools.misc import clean_context, format_date
import logging


_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    qty = fields.Integer('Qty', default=1)
    uom_id = fields.Many2one('uom.uom', string='UoM')


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    team_id = fields.Many2one('department.team', string='Team')
    date = fields.Date('Date', default=fields.Date.today())
    state = fields.Selection(selection_add=[
        ('to_approved', 'To Be Approved'), 
        ('need_improvement', 'Need Improvement'),
    ], ondelete={
        'to_approved': 'cascade',
        'need_improvement': 'cascade',
    }, string='Status')
    type = fields.Selection([
        ('office', 'Office Stationery'),
        ('service', 'Service'),
        ('inventory', 'Inventory'),
        ('vehicle', 'Vehicle'),
        ('other', 'Other'),
    ], string='Type', required=True, default='office', tracking=True)
    approval_ids = fields.One2many(comodel_name='approval.request', inverse_name='expense_id', string='Approval Request', readonly=True, copy=False, tracking=True)
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', readonly=True)
    approved_date = fields.Datetime('Approved Date', compute='_compute_approved_date', readonly=True, store=True)

    @api.depends('approval_ids', 'approval_ids.request_status')
    def _compute_approved_date(self):
        for record in self:
            if record.approval_ids:
                request = record.approval_ids[record.approval_count-1]
                if request.request_status == 'approved':
                    record.approved_date = request.date_confirmed
                else:
                    record.approved_date = ''

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.mapped('approval_ids'))

    def _generate_mail_activity(self, user, batch):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('hr_expense.model_hr_expense_sheet').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'date_deadline': fields.Date.today(),
            'user_id': user.id,
            'summary': 'Please process the following expenses as soon as possible. Thank You!',
            'batch': batch,
            'handle_by': 'just_one',
        })

    def _send_notification_to_team(self):
        self.ensure_one()
        batch = self.env['ir.sequence'].next_by_code('assignment.activity')
        if self.team_id:
            # create mail.activity
            for user in self.team_id.member_ids:
                self._generate_mail_activity(user, batch)

    def generate_approval_request(self):
        self.ensure_one()
        category_pr = self.env.company.approval_expense_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'expense_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for {self.name} from {self.employee_id.name}"
        }
        self.sudo().write({ 'state': 'submit' })
        request = self.env['approval.request'].create(vals)
        query = f"UPDATE approval_approver SET user_id={self.employee_id.parent_id.user_id.id} WHERE request_id={request.id} AND user_id=2"
        self.env.cr.execute(query)
        request.action_confirm()

    def action_view_approval_request(self):
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        if self.approval_count == 0:
            return
        elif self.approval_count == 1:
            action['views'] = [(self.env.ref('approvals.approval_request_view_form').id, 'form')]
            action['res_id'] = approvals.ids[0]
        elif self.approval_count > 1:
            action['domain'] = [('id', 'in', approvals.ids)]
        return action

    def action_approved(self):
        self.ensure_one()
        # self.action_submit_sheet()
        self.approve_expense_sheets()

    def action_need_improvement(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('hr_expense.model_hr_expense_sheet').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.employee_id.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'need_improvement' })

    def approve_expense_sheets(self):
        res = super(HrExpenseSheet, self).approve_expense_sheets()
        self._send_notification_to_team()
        return res

    def reset_expense_sheets(self):
        res = super().reset_expense_sheets()
        self.mapped('approval_ids').filtered(lambda approval: approval.request_status == 'pending').action_cancel()
        return res