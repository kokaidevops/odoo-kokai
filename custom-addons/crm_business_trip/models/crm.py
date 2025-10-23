from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CRMBusinessTrip(models.Model):
    _name = 'crm.business.trip'
    _description = 'CRM Business Trip'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user.id, required=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
    partner_id = fields.Many2one('res.partner', string='Partner', domain="[('customer_rank','>', 0)]")
    name = fields.Char('Name')
    date = fields.Date('Date', default=fields.Date.today(), required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id.id, required=True)
    employee_job_id = fields.Many2one('hr.job', string='Employee Job', related='employee_id.job_id')
    employee_department_id = fields.Many2one('hr.department', string='Employee Department', related='employee_id.department_id')
    destination_id = fields.Many2one('res.city', string='Destination City', required=True)
    start_date = fields.Date('Start Date', default=fields.Date.today(), required=True)
    end_date = fields.Date('End Date', default=fields.Date.today(), required=True)
    manager_id = fields.Many2one('hr.employee', string='Assign By', default=lambda self: self.env.user.employee_id.parent_id.id, required=True)
    manager_job_id = fields.Many2one('hr.job', string='Assignor Job', related='manager_id.job_id')
    manager_department_id = fields.Many2one('hr.department', string='Assignor Department', related='manager_id.department_id')
    purpose = fields.Text('Purpose', default="""Perdin DN/Perdin LN : Canvassing ke beberapa Customer di Kalimantan Tengah untuk kebutuhan Reserach Produk""")
    partisan_ids = fields.Many2many('hr.employee', string='Partisan')
    mode = fields.Selection([
        ('company_vehicle', 'Company Vehicle'),
        ('land_vehicle', 'Land Vehicle'),
        ('marine_vehicle', 'Marine Vehicle'),
        ('air_vehicle', 'Air Vehicle'),
    ], string='Mode', default='company_vehicle', required=True)
    accommodation = fields.Selection([
        ('hotel', 'Hotel'),
        ('lodging', 'Lodging'),
        ('rental_house', 'Rental House'),
        ('mess', 'Mess'),
        ('private_house', 'Own House'),
    ], string='Accommodation', required=True, default='hotel')
    category = fields.Selection([
        ('reimbursement', 'Reimbursement'),
        ('cash', 'Cash'),
    ], string='Category', default='cash', required=True)
    cost_ids = fields.One2many('business.trip.cost', 'trip_id', string='Cost')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    approval_ids = fields.One2many('approval.request', 'trip_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True, readonly=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('crm.business.trip')
        return super(CRMBusinessTrip, self).create(vals)

    def action_draft(self):
        self.mapped('cost_ids').action_draft()
        self.write({ 'state': 'draft' })

    def action_request(self):
        self.generate_approval_request()
        self.write({ 'state': 'request' })

    def action_approved(self):
        self.mapped('cost_ids').filtered(lambda line: line.state == 'draft').action_approved()
        self.write({ 'state': 'approved' })

    def action_rejected(self, reason):
        self.write({ 'state': 'rejected' })
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('crm_business_trip.model_crm_business_trip').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })

    def button_cancel(self):
        self.mapped('cost_ids').action_rejected()
        self.write({ 'state': 'cancel' })

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def action_show_approval_request(self):
        action = self.env.ref('approvals.approval_request_action').read()[0]
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    @api.depends('cost_ids', 'cost_ids.total_amount')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = sum([ cost.total_amount for cost in record.cost_ids ])

    def generate_approval_request(self):
        approved_request = self.approval_ids.filtered(lambda approval: approval.request_status == 'approved')
        if approved_request:
            raise ValidationError("This Request has been Approved! Can't request approval again!")
        try:
            self.sudo().write({ 'state': 'request' })

            category_pr = self.env.company.approval_business_trip_id
            vals = {
                'name': 'Request Approval for ' + self.name,
                'trip_id': self.id,
                'request_owner_id': self.env.user.id,
                'category_id': category_pr.id,
                'reason': f"Request Approval for {self.name} from {self.user_id.name} \n {self.purpose or ''}"
            }
            request = self.env['approval.request'].sudo().create(vals)
            query = f"UPDATE approval_approver SET user_id={self.department_id.manager_id.user_id.id} WHERE request_id={request.id} AND user_id=2"
            self.env.cr.execute(query)
            request.action_confirm()
        except Exception as e:
            raise ValidationError("Can't Request Approval. Please Contact Administrator. \n%s" % str(e))


class BusinessTripCost(models.Model):
    _name = 'business.trip.cost'
    _description = 'Business Trip Cost'

    trip_id = fields.Many2one('crm.business.trip', string='Trip', ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', related='trip_id.company_id')
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', string='Category', domain="[('can_be_expensed', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    duration = fields.Float('Duration', default=1)
    value = fields.Float('Value')
    total_amount = fields.Float('Total Amount', compute='_compute_total_amount')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='State', required=True, default='draft')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            record.name = record.product_id.display_name

    @api.depends('duration', 'value')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.value*record.duration

    def action_draft(self):
        self.write({ 'state': 'draft' })

    def action_approved(self):
        self.write({ 'state': 'approved' })

    def action_rejected(self):
        if not self.state == 'approved':
            self.write({ 'state': 'rejected' })


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    trip_ids = fields.One2many('crm.business.trip', 'opportunity_id', string='Business Trip')
    trip_count = fields.Integer('Trip Count', compute='_compute_trip_count', store=True)

    @api.depends('trip_ids')
    def _compute_trip_count(self):
        for record in self:
            record.trip_count = len(record.trip_ids)

    def action_show_business_trip(self):
        action = self.env.ref('crm_business_trip.crm_business_trip_action').read()[0]
        action['domain'] = [('id', 'in', self.trip_ids.ids)]
        action['context'] = {
            'default_opportunity_id': self.id,
            'default_partner_id': self.partner_id.id,
        }
        return action


class ResPartner(models.Model):
    _inherit = 'res.partner'

    trip_ids = fields.One2many('crm.business.trip', 'partner_id', string='Business Trip')
    # trip_count = fields.Integer('Trip Count', compute='_compute_trip_count', store=True)

    @api.depends('trip_ids')
    def _compute_trip_count(self):
        for record in self:
            record.trip_count = len(record.trip_ids)

    def action_show_business_trip(self):
        action = self.env.ref('crm_business_trip.crm_business_trip_action').read()[0]
        action['domain'] = [('id', 'in', self.trip_ids.ids)]
        action['context'] = {
            'default_id': self.id,
        }
        return action
