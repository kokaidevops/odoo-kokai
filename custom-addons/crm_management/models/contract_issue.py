from odoo import _, api, fields, models

class ContractIssue(models.Model):
    _name = 'contract.issue'
    _description = 'Issue in FIR or FRK'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'issue_date'

    order_id = fields.Many2one('sale.order', string='Order', tracking=True)
    opportunity_id = fields.Many2one('crm.lead', string='Lead', tracking=True)
    name = fields.Char('Issue', default='Issue for Release', tracking=True)
    issue_date = fields.Datetime('Issue Date', default=fields.Datetime.now(), tracking=True)
    description = fields.Text('Description', default='-', tracking=True)
    issue_solve = fields.Text('Issue Solve', default='-', tracking=True)
    solve_date = fields.Datetime('Solve Date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('approved', 'Approved'),
        ('reject', 'Reject'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Prepared', default=lambda self: self.env.user.id, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    document = fields.Selection([
        ('inquiry', 'Inquiry'),
        ('contract', 'Contract'),
    ], string='Document', required=True, default='inquiry', tracking=True)
    approval_ids = fields.One2many('approval.request', 'issue_id', string='Approval')
    approved_date = fields.Datetime('Approval Date', compute='_compute_approved_date')

    @api.depends('approval_ids', 'approval_ids.request_status')
    def _compute_approved_date(self):
        for record in self:
            if record.approval_ids:
                request = record.approval_ids[0]
                if request.request_status == 'approved':
                    record.approved_date = request.date_confirmed

    def generate_approval_request(self):
        self.ensure_one()
        category_pr = self.env.company.issue_approval_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'issue_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for {self.name} from {self.user_id.name} \n Issue in {self.order_id.name} has been done solved with solution is {self.issue_solve}\nPlease review and approved or refused"
        }
        request = self.env['approval.request'].create(vals)
        query = f"UPDATE approval_approver SET user_id={self.user_id.department_id.manager_id.user_id.id} WHERE request_id={request.id} AND user_id=2"
        self.env.cr.execute(query)
        request.action_confirm()

    def action_request(self):
        self.ensure_one()
        self.generate_approval_request()
        self.write({ 'state': 'request' })

    def action_approved(self):
        self.ensure_one()
        self.write({ 'state': 'approved' })

    def action_reject(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('crm_management.model_contract_issue').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_notification').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'reject' })

    def action_cancel(self):
        self.ensure_one()
        if self.approval_ids:
            request = self.approval_ids[0]
            request.action_cancel()
        self.write({ 'state': 'cancel' })