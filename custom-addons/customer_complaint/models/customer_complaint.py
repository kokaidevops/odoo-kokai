from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ComplaintLine(models.Model):
    _name = 'complaint.line'
    _description = 'Complaint Line'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True)
    
    complaint_id = fields.Many2one('customer.complaint', string='Complaint', tracking=True)
    name = fields.Char('Name', tracking=True)
    complaint = fields.Html('Complaint', tracking=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('line.complaint')
        return super(ComplaintLine, self).create(vals)


class ComplaintCauses(models.Model):
    _name = 'complaint.causes'
    _description = 'Complaint Causes'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True)
    
    complaint_id = fields.Many2one('customer.complaint', string='Complaint', tracking=True)
    line_id = fields.Many2one('complaint.line', string='Complaint', domain="[('complaint_id', '=', complaint_id)]", tracking=True)
    causes = fields.Text('Analysis of Causes', tracking=True)


class ComplaintSolution(models.Model):
    _name = 'complaint.solution'
    _description = 'Complaint Solution'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True)
    
    complaint_id = fields.Many2one('customer.complaint', string='Complaint', tracking=True)
    line_id = fields.Many2one('complaint.line', string='Complaint', domain="[('complaint_id', '=', complaint_id)]", tracking=True)
    settlement_solution = fields.Text('Settlement Solution', tracking=True)


class ComplaintCorrective(models.Model):
    _name = 'complaint.corrective'
    _description = 'Complaint Corrective'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    date = fields.Date('Date', default=fields.Date.today())
    
    complaint_id = fields.Many2one('customer.complaint', string='Complaint', tracking=True)
    line_id = fields.Many2one('complaint.line', string='Complaint', domain="[('complaint_id', '=', complaint_id)]", tracking=True)
    corrective_action = fields.Text('Corrective Action')


class CustomerComplaint(models.Model):
    _name = 'customer.complaint'
    _description = 'Customer Complaint'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, tracking=True)

    management_id = fields.Many2one('res.users', string='Management', related='company_id.director_id')
    name = fields.Char('Name', tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    product_ids = fields.Many2many('product.product', string='Product', tracking=True)
    qty = fields.Integer('Qty', tracking=True)
    contract_no = fields.Char('Contract No', tracking=True)
    complaint_ids = fields.One2many('complaint.line', 'complaint_id', string='Complaint', tracking=True)
    loss_detail = fields.Text('Loss Detail', tracking=True)
    loss = fields.Float('Loss', tracking=True)
    causes_ids = fields.One2many('complaint.causes', 'complaint_id', string='Analysis of Causes', tracking=True)
    solution_ids = fields.One2many('complaint.solution', 'complaint_id', string='Settlement Solution', tracking=True)
    corrective_ids = fields.One2many('complaint.corrective', 'complaint_id', string='Corrective Action', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('analysis', 'Analysis'),
        ('closed', 'Closed'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True, tracking=True)
    closing_date = fields.Date('Closing Date', tracking=True)
    verification = fields.Text('Verification', tracking=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('customer.complaint')
        return super(CustomerComplaint, self).create(vals)

    def action_open(self):
        self.ensure_one()
        self.write({ 'state': 'open' })

    def action_analysis(self):
        self.ensure_one()
        department_ids = self.emv['hr.department'].search([])
        assignment = self.env['assignment.task'].create({
            'user_id': self.env.user.id,
            'assigned_to': 'department',
            'subject': 'Notification about New Customer Complaint',
            'description': f"",
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'department_ids': department_ids.ids,
            'employee_type_ids': [self.env.ref('department_detail.hr_contract_type_head_of_department')],
            'model': 'customer.complaint',
            'res_id': self.id,
        })
        if not assignment:
            raise ValidationError("Can't Assignment Task! Please contact Administrator!")
        assignment.action_assign()
        self.write({ 'state': 'analysis' })

    def action_closed(self):
        self.ensure_one()
        self.write({ 'state': 'closed', 'closing_date': fields.Date.today() })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })
    
    def action_request_verification(self):
        self.ensure_one()
        assignment = self.env['assignment.task'].create({
            'user_id': self.env.user.id,
            'assigned_to': 'employee',
            'subject': 'Notification about Request Verification Customer Complaint',
            'description': f"",
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'user_ids': [self.management_id.id],
            'model': 'customer.complaint',
            'res_id': self.id,
        })
        if not assignment:
            raise ValidationError("Can't Assignment Task! Please contact Administrator!")
        assignment.action_assign()
