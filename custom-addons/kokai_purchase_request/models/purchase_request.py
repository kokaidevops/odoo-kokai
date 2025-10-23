from odoo import _, api, fields, models, http
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    request_ids = fields.Many2many(
        comodel_name='purchase.request',
        relation='custom_purchase_request_purchase_order_rel',
        column1='purchase_order_id',
        column2='purchase_request_id',
        readonly=True,
        copy=False,
    )


class PurchaseRequestType(models.Model):
    _name = 'purchase.request.type'
    _description = 'Type of Purchase Request'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    @api.model
    def _default_domain_team(self):
        return [('department_id', '=', self.env.ref('department_detail.hr_management_data_purchasing').id)]

    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_department_id', store=True)
    due_date = fields.Date('Due Date', tracking=True, required=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'ASAP'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', required=True, default='0')
    request_type = fields.Selection([
        ('goods', 'Goods'),
        ('services', 'Services'),
    ], string='Type', default='goods', required=True)
    type = fields.Selection([
        ('project', 'Project'),
        ('non_project', 'Non Project'),
    ], string='Description', required=True, default='non_project', tracking=True)
    team_id = fields.Many2one('department.team', string='Purchase Team', required=True, domain=_default_domain_team, tracking=True, default=lambda self: self.env.company.default_purchase_team_id.id)
    attachment_ids = fields.Many2many('ir.attachment', string='File')
    order_ids = fields.Many2many(
        comodel_name='purchase.order', 
        relation='custom_purchase_request_purchase_order_rel',
        column1='purchase_request_id',
        column2='purchase_order_id',
        string='Purchase Order',
        readonly=True,
        copy=False,
    )

    @api.depends('requested_by')
    def _compute_department_id(self):
        for record in self:
            record.department_id = record.requested_by.department_id.id

    def _generate_mail_activity(self, user, batch):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('purchase_request.model_purchase_request').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('kokai_purchase_request.mail_activity_type_data_process_pr').id,
            'date_deadline': self.due_date,
            'user_id': user.id,
            'summary': 'Please process the following Purchase Request as soon as possible. Thank You!',
            'batch': batch,
            'handle_by': 'just_one',
        })

    def button_in_progress(self):
        # request to purchasing team
        if self.env.context.get('generate_mail_activity'):
            batch = self.env['ir.sequence'].next_by_code('assignment.activity')
            if self.team_id:
                for user in self.team_id.member_ids:
                    self._generate_mail_activity(user, batch)
        return super(PurchaseRequest, self).button_in_progress()

    @api.onchange('group_id')
    def _onchange_group_id(self):
        for record in self:
            record.write({ 'origin': record.group_id.name or '' })

    def _generate_name(self):
        name = self.name
        if self.department_id:
            sequence = self.env['ir.sequence.department'].sudo().search([
                ('department_id.id', '=', self.department_id.id),
                ('model_id.model', '=', 'purchase.request'),
            ], limit=1)
            if sequence:
                name = self.env['ir.sequence'].next_by_code(sequence.sequence_id.code)
        return name

    def button_to_approve(self):
        self.name = self._generate_name()
        return super().button_to_approve()


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    link = fields.Char('Link')
    reason = fields.Char('Reason')
    suggested = fields.Char('Item/Supplier')
    drawing = fields.Binary('Drawing')