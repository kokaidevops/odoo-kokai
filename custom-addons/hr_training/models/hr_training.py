from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AnnualTraining(models.Model):
    _name = 'annual.training'
    _description = 'Annual Training'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    active = fields.Boolean('Active', default=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    
    name = fields.Char('Name', default='New Annual Training')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('need_improvement', 'Need Improvement'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft', tracking=True)
    
    training_ids = fields.One2many('hr.training', 'annual_id', string='Training')
    training_count = fields.Integer('Training Count', compute='_compute_training_count', store=True)
    @api.depends('training_ids')
    def _compute_training_count(self):
        for record in self:
            record.training_count = len(record.training_ids)
    
    def action_show_training(self):
        self.ensure_one()
        if self.training_count == 0:
            return
        action = self.env.ref('hr_training.hr_training_action').read()[0]
        action['domain'] = [('id', 'in', self.training_ids.ids)]
        return action

    approval_ids = fields.One2many('approval.request', 'annual_training_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)
    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)
    
    def action_show_approval(self):
        self.ensure_one()
        if self.approval_count == 0:
            return
        action = self.env.ref('approvals.approval_request_action_all').read()[0]
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_requested(self):
        self.ensure_one()
        category_pr = self.env.ref('hr_training.approval_category_data_annual_training')
        vals = {
            'name': 'Request Approval for ' + self.name,
            'annual_training_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for Annual Training Plan {self.name} from {self.user_id.name} \n Annual Training Plan {self.name}"
        }
        request = self.env['approval.request'].create(vals)
        request.action_confirm()
        self.write({ 'state': 'requested' })

    def action_approved(self):
        self.ensure_one()
        notification = self.env['schedule.task'].sudo().create({
            'company_id': self.env.company.id,
            'subject': 'Notifikasi Approved Annual Training',
            'user_id': self.user_id.id,
            'assign_by_id': 1,
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'description': f"Kepada {self.user_id.name} \n Annual Training {self.name} yang diajukan disetujui. Silahkan lanjutkan ke proses berikutnya. \n Terima Kasih",
            'date': fields.Date.today(),
            'start_date': fields.Datetime.now(),
            'stop_date': fields.Datetime.now(),
            'state': 'draft',
            'type': 'notification',
            'model': 'annual.training',
            'res_id': self.id,
        })
        notification.action_assign()
        self.sudo().write({ 'state': 'approved' })
        for training in self.training_ids:
            training.action_planning()

    def action_need_improvement(self):
        self.ensure_one()
        self.write({ 'state': 'need_improvement' })
        notification = self.env['schedule.task'].sudo().create({
            'company_id': self.env.company.id,
            'subject': 'Notifikasi Refused Annual Training',
            'user_id': self.user_id.id,
            'assign_by_id': 1,
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'description': f"Kepada {self.user_id.name} \n Annual Training {self.name} yang diajukan ditolak. Silahkan ditinjau kembali dan diperbaiki sesuai dengan catatan penolakan yang telah dicantumkan. \n Terima Kasih",
            'date': fields.Date.today(),
            'start_date': fields.Datetime.now(),
            'stop_date': fields.Datetime.now(),
            'state': 'draft',
            'type': 'notification',
            'model': 'annual.training',
            'res_id': self.id,
        })
        notification.action_assign()

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('annual.training')
        return super(AnnualTraining, self).create(vals)


class HRTraining(models.Model):
    _name = 'hr.training'
    _description = 'HR Training'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', default='New Training')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    annual_id = fields.Many2one('annual.training', string='Annual Training Plan')
    date = fields.Date('Date', default=fields.Date.today(), tracking=True)
    method_ids = fields.Many2many('hr.training.method', string='Method')
    content_id = fields.Many2one('hr.training.content', string='Content', tracking=True)
    content = fields.Text('Detail Content', tracking=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    target = fields.Integer('Target', tracking=True) # ?
    hour = fields.Float('Hour', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planning', 'Planning'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft', tracking=True)
    attendance_type = fields.Selection([
        ('all', 'All'),
        ('department', 'Department'),
        ('employee', 'Employee'),
    ], string='Attendance Type', default='all', tracking=True)
    department_ids = fields.Many2many('hr.department', string='Department')
    participant_ids = fields.Many2many('res.users', string='Participant')
    attendance_ids = fields.One2many('hr.training.attendance', 'training_id', string='Attendance')
    performance_date = fields.Datetime('Performance Date', tracking=True)
    done_date = fields.Datetime('Done Date', tracking=True)
    note = fields.Text('Note', placeholder="Note in Training", tracking=True)

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_planning(self):
        self.ensure_one()
        if not self.state == 'cancel':
            domain = [ ('active', '=', True) ]
            if self.attendance_type == 'department':
                domain.append(('department_id', 'in', self.department_ids.ids))
            if self.attendance_type == 'employee':
                domain.append(('id', 'in', self.participant_ids.ids))

            users = self.env['res.users'].search(domain)
            for user in users:
                self.env['hr.training.attendance'].create({
                    'training_id': self.id,
                    'participant_id': user.id,
                })
            self.write({ 'state': 'planning' })

    def action_progress(self):
        self.ensure_one()
        self.write({ 'state': 'progress', 'performance_date': fields.Datetime.now() })

    def action_done(self):
        self.ensure_one()
        self.write({ 'state': 'done', 'done_date': fields.Datetime.now() })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })
    
    @api.onchange('content_id')
    def _onchange_content_id(self):
        for record in self:
            record.write({
                'content': record.content_id.description,
                'responsible_id': record.content_id.responsible_id.id,
            })

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('hr.training')
        return super(HRTraining, self).create(vals)

    def action_attendance(self):
        self.ensure_one()
        attendance = self.env['hr.training.attendance'].search([
            ('training_id', '=', self.id),
            ('participant_id', '=', self.env.user.id),
        ])
        if attendance:
            attendance.write({ 'attendance': 'yes' })


class HRTrainingContent(models.Model):
    _name = 'hr.training.content'
    _description = 'HR Training Content'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name', tracking=True)
    description = fields.Text('Description', tracking=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', tracking=True)


class HRTrainingMethod(models.Model):
    _name = 'hr.training.method'
    _description = 'HR Training Method'

    name = fields.Char('Name')


class HRTrainingAttendance(models.Model):
    _name = 'hr.training.attendance'
    _description = 'HR Training Attendance'

    training_id = fields.Many2one('hr.training', string='Training')
    participant_id = fields.Many2one('res.users', string='Participant')
    attendance_date = fields.Datetime('Attendance Date')
    attendance = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Attendance')
    remark = fields.Char('Remark')