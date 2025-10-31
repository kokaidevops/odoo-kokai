from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError


class RecruitmentRequest(models.Model):
    _name = 'recruitment.request'
    _description = 'Recruitment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def name_get(self):
        return [(record.id, f"[{record.name}] {record.job_id.name}-{record.employee_type_id.code}") for record in self]

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('recruitment.request')
        return super(RecruitmentRequest, self).create(vals)

    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    
    name = fields.Char('Name', default='New Request', readonly=True)
    request_by_id = fields.Many2one('res.users', string='Request By', default=lambda self: self.env.user.id)
    department_id = fields.Many2one('hr.department', string='Department', default=lambda self: self.env.user.department_id.id, tracking=True)
    job_id = fields.Many2one('hr.job', string='Job', domain="[('department_id', '=', department_id)]", tracking=True)
    employee_type_id = fields.Many2one('hr.contract.type', string='Employee Type')
    target = fields.Integer('Target', default=1, tracking=True)
    request_date = fields.Datetime('Request Date', default=fields.Datetime.now(), tracking=True)
    due_date = fields.Date('Due Date', tracking=True)
    specification = fields.Html('Employee Specification', related='job_id.description', readonly=False, store=True)

    reason_for_recruitment = fields.Selection([
        ('new', 'New'),
        ('replacement', 'Replacement'),
    ], string='Reason For Recruitment', default='new', tracking=True)
    reason = fields.Char('Reason')
    old_user_id = fields.Many2one('res.users', string='Old User', domain="[('department_id', '=', department_id)]")

    progressing_date = fields.Datetime('Progressing Date', tracking=True)
    closing_date = fields.Date('Closing Date', tracking=True)
    priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
    ], string='Priority', default='0', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Request Approval'),
        ('approved', 'Approved'),
        ('on_progress', 'On Progress'),
        ('closed', 'Closed'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft')
    team_id = fields.Many2one('department.team', string='Team')

    applications_ids = fields.One2many('hr.applicant', 'request_id', string='Applications')
    applications_count = fields.Integer('Applications Count', compute='_compute_applications_count', store=True)
    applications_join_count = fields.Integer('Applications Join', compute='_compute_applications_count', store=True)
    @api.depends('applications_ids', 'applications_ids.stage_id')
    def _compute_applications_count(self):
        for record in self:
            record.applications_count = len(record.applications_ids)
            record.applications_join_count = len(record.applications_ids.filtered(lambda applicant: applicant.stage_id.id == self.env.ref('hr_recruitment.stage_job5').id))
            if len(record.applications_ids) > 0:
                record.state = 'on_progress'
            if len(record.applications_ids.filtered(lambda applicant: applicant.stage_id.id == self.env.ref('hr_recruitment.stage_job5').id)) == record.target:
                record.state = 'closed'

    def action_show_applications(self):
        self.ensure_one()
        action = self.env.ref('hr_recruitment.crm_case_categ0_act_job').sudo().read()[0]
        action['domain'] = [('id', 'in', self.applications_ids.ids)]
        return action

    approval_ids = fields.One2many('approval.request', 'recruitment_request_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)
    approved_date = fields.Datetime('Approved Date', compute='_compute_approved_date', store=True)
    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    @api.depends('approval_ids', 'approval_ids.request_status')
    def _compute_approved_date(self):
        for record in self:
            request = record.approval_ids.filtered(lambda approval: approval.request_status == 'approved')
            record.approved_date = '' if len(request) == 0 else request[len(request)-1].date_confirmed
        
    def action_show_approval(self):
        self.ensure_one()
        if self.approval_count == 0:
            return
        action = self.env.ref('approvals.approval_request_action_all').read()[0]
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    def generate_approval_request(self):
        self.ensure_one()
        category_pr = self.env.company.recruitment_request_approval_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'recruitment_request_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for {self.name} from {self.request_by_id.name} \n Recruitment {self.target} Employee(s) for {self.name}"
        }
        request = self.env['approval.request'].create(vals)
        request.action_confirm()
        self.sudo().write({ 'state': 'requested' })

    def action_request(self):
        self.ensure_one()
        for user in self.team_id.member_ids:
            self.env['mail.activity'].create({
                'res_model_id': self.env.ref('recruitment_request.model_recruitment_request').id,
                'res_id': self._origin.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': fields.Date.today(),
                'user_id': user.id,
                'summary': "Please process this request",
                'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
                'handle_by': 'just_one',
            })

    def action_approved(self):
        self.ensure_one()
        self.write({'state': 'approved'})
        self.action_request()

    def action_refused(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('recruitment_request.model_recruitment_request').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.employee_id.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'refused' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel'})
        # delete all activity
        query = "DELETE FROM mail_activity WHERE res_model_id=%s AND res_id=%s" %(self.env.ref('recruitment_request.model_recruitment_request').id, self._origin.id)
        self.env.cr.execute(query)


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    request_id = fields.Many2one('recruitment.request', string='Request', domain=[('state', '=', 'on_progress')])
    job_id = fields.Many2one('hr.job', related='request_id.job_id', store=True, readonly=False)

    @api.onchange('request_id')
    def _onchange_request_id(self):
        for record in self:
            if record.request_id and record.request_id.state not in ['approved', 'on_progress']:
                raise ValidationError("Can't add applicant to Request Closed")

    @api.depends('stage_id')
    def _generate_employee_template(self):
        pass
        user = self.env['res.users'].create({
            'name': self.name,
            'login': self.email_from,
            'partner_id': self.partner_id.id,
        })
        user.action_create_employee()