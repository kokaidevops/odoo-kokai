from odoo import _, api, fields, models


class OhsNonconformity(models.Model):
    _name = 'ohs.nonconformity'
    _description = 'OHS Nonconformity'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name', default="New")
    user_id = fields.Many2one('res.users', string='Auditor', default=lambda self: self.env.user.id)
    audite_id = fields.Many2one('res.users', string='Audite')
    nonconformity_id = fields.Many2one('nonconformity.patrol', string='Nonconformity')
    date = fields.Date('Issue Date', default=fields.Date.today())
    nonconformity = fields.Text('Non Conformity')
    suggestions = fields.Text('Suggestions')
    reason = fields.Text('Reason')
    corrective_ids = fields.One2many('corrective.ohs.nonconformity', 'ohs_nonconformity_id', string='Corrective')
    preventive_ids = fields.One2many('preventive.ohs.nonconformity', 'ohs_nonconformity_id', string='Preventive')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('request', 'Request'),
        ('approved', 'Done'),
        ('need_improvement', 'Need Improvement'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft')
    note = fields.Text('Note')
    category = fields.Selection([
        ('A', 'It is very important to complete it at that time. (Stop Activity)'),
        ('B', 'Must be completed within a certain time (According to Deadline)'),
        ('C', 'Completed with flexible time'),
        ('D', 'Delegation, completing work by asking for help from colleagues, but the work remains the responsibility of the PIC.'),
        ('E', 'No need to do it'),
    ], string='Category', default='B')

    approval_ids = fields.One2many('approval.request', 'ohs_nonconformity_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_ids')
        
    def action_show_approval(self):
        self.ensure_one()
        if self.approval_count == 0:
            return
        action = self.env.ref('approvals.approval_request_action_all').read()[0]
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    @api.depends('approval_ids')
    def _compute_approval_ids(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if 'name' not in val or val['name'] == 'New':
                val['name'] = self.env['ir.sequence'].next_by_code('ohs.nonconformity')
        return super(OhsNonconformity, self).create(vals)

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_open(self):
        self.ensure_one()
        notification = self.env['schedule.task'].sudo().create({
            'company_id': self.env.company.id,
            'subject': 'Notifikasi Temuan NC',
            'user_id': self.audite_id.id,
            'assign_by_id': 1,
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'description': f"Kepada {self.audite_id.name} \nLaporan NC {self.name} pada tanggal {self.date}. Silahkan menyelesaikan NC yang telah ditemukan pada area Anda. \nTerima Kasih",
            'date': fields.Date.today(),
            'start_date': fields.Datetime.now(),
            'stop_date': fields.Datetime.now(),
            'state': 'draft',
            'type': 'notification',
            'model': 'ohs.nonconformity',
            'res_id': self.id,
        })
        notification.action_assign()
        self.write({ 'state': 'open' })

    def action_request(self):
        self.ensure_one()
        category_pr = self.env.ref('ohs_inspection.approval_category_data_ohs_nonconformity')
        vals = {
            'name': 'Request Approval for ' + self.name,
            'issue_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Permintaan persetujuan untuk penyelesaian {self.name} dari {self.audite_id.name} \nKepada Auditor, \nKetidaksesuaian yang ditemukan oleh Auditor telah diselesaikan. Mohon untuk mengecek laporan yang telah diseratakan."
        }
        self.sudo().write({ 'approval_ids': [(0, 0, vals)] })
        request = self.approval_ids[len(self.approval_ids)-1]
        request.action_confirm()
        self.write({ 'state': 'request' })

    def action_approved(self):
        self.ensure_one()
        self.write({ 'state': 'approved' })

    def action_need_improvement(self):
        self.ensure_one()
        notification = self.env['schedule.task'].sudo().create({
            'company_id': self.env.company.id,
            'subject': 'Notifikasi Penolakan Penyelesaian NC',
            'user_id': self.audite_id.id,
            'assign_by_id': 1,
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'description': f"Kepada {self.audite_id.name} \n Laporan Penyelesaian NC {self.name} telah ditolak. Silahkan memperbaiki laporan sesuai dengan alasan penolakan yang telah disertakan.",
            'date': fields.Date.today(),
            'start_date': fields.Datetime.now(),
            'stop_date': fields.Datetime.now(),
            'state': 'draft',
            'type': 'notification',
            'model': 'ohs.nonconformity',
            'res_id': self.id,
        })
        notification.action_assign()
        self.write({ 'state': 'need_improvement' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })


class CorrectiveOhsNonconformity(models.Model):
    _name =  'corrective.ohs.nonconformity'
    _description =  'Corrective Ohs Nonconformity'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Corrective')
    ohs_nonconformity_id = fields.Many2one('ohs.nonconformity', string='Accident')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    due_date = fields.Date('Due Date')
    completion_date = fields.Date('Completion Date')
    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Done'),
    ], string='State', default='open', required=True)

    def action_open(self):
        self.ensure_one()
        self.write({ 'state': 'open' })

    def action_done(self):
        self.ensure_one()
        self.write({ 'completion_date': fields.Date.today(), 'state': 'done' })


class PreventiveOhsNonconformity(models.Model):
    _name =  'preventive.ohs.nonconformity'
    _description =  'Preventive Ohs Nonconformity'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Preventive')
    ohs_nonconformity_id = fields.Many2one('ohs.nonconformity', string='Accident')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    due_date = fields.Date('Due Date')
    completion_date = fields.Date('Completion Date')
    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Done'),
    ], string='State', default='open', required=True)

    def action_open(self):
        self.ensure_one()
        self.write({ 'state': 'open' })

    def action_done(self):
        self.ensure_one()
        self.write({ 'completion_date': fields.Date.today(), 'state': 'done' })