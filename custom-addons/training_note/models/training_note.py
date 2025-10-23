from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TrainingNote(models.Model):
    _name = 'training.note'
    _description = 'Training Note'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    active = fields.Boolean('Active', default=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    name = fields.Char('Name', default='New Note')
    date = fields.Datetime('Date', tracking=True, default=fields.Datetime.now())
    training_id = fields.Many2one('hr.training', string='Training', tracking=True)
    responsible_id = fields.Many2one('res.users', string='Responsible', related='training_id.responsible_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft', tracking=True)
    summary = fields.Html('Summary')
    evaluation = fields.Html('Evaluation')

    test_date = fields.Date('Test Date', tracking=True)
    min_value = fields.Float('Min Value')
    avg_value = fields.Float('Average Value', compute='_compute_average_value', store=True)
    grad_percentage = fields.Float('Passed Percentage', compute='_compute_grad_percentage', store=True)

    @api.depends('result_ids.value')
    def _compute_grad_percentage(self):
        for record in self:
            if len(record.result_ids) == 0:
                record.grad_percentage = 0
            else:
                record.grad_percentage = sum([1 if result.value >= record.min_value else 0 for result in record.result_ids])/len(record.result_ids)

    @api.depends('result_ids.value')
    def _compute_average_value(self):
        for record in self:
            if len(record.result_ids) == 0:
                record.avg_value = 0
            else:
                record.avg_value = sum([result.value for result in record.result_ids])/len(record.result_ids)
    
    result_ids = fields.One2many('hr.training.result', 'note_id', string='Result')

    attachment_ids = fields.Many2many('ir.attachment', string='Attachment')

    approval_ids = fields.One2many('approval.request', 'training_note_id', string='Approval')
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
        category_pr = self.env.ref('training_note.approval_category_data_training_note')
        vals = {
            'name': 'Request Approval for ' + self.name,
            'training_note_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for Training Note {self.name} from {self.user_id.name} \n Training Note {self.name}"
        }
        request = self.env['approval.request'].create(vals)
        request.action_confirm()
        self.write({ 'state': 'requested' })

    def action_approved(self):
        self.ensure_one()
        self.write({ 'state': 'approved' })

    def action_refused(self):
        self.ensure_one()
        notification = self.env['schedule.task'].sudo().create({
            'company_id': self.env.company.id,
            'subject': 'Notifikasi Refused Training Note',
            'user_id': self.user_id.id,
            'assign_by_id': 1,
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'description': f"Kepada {self.user_id.name} \n Training Note {self.name} yang diajukan ditolak. Silahkan ditinjau kembali dan diperbaiki sesuai dengan catatan penolakan yang telah dicantumkan. \n Terima Kasih",
            'date': fields.Date.today(),
            'start_date': fields.Datetime.now(),
            'stop_date': fields.Datetime.now(),
            'state': 'draft',
            'type': 'notification',
            'model': 'training.note',
            'res_id': self.id,
        })
        notification.action_assign()
        self.write({ 'state': 'refused' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('training.note')
        return super(TrainingNote, self).create(vals)


class HRTrainingResult(models.Model):
    _name = 'hr.training.result'
    _description = 'HR Training Result'

    note_id = fields.Many2one('training.note', string='Note')
    training_id = fields.Many2one('hr.training', string='Training', related='note_id.training_id')
    participant_id = fields.Many2one('res.users', string='Participant')
    department_id = fields.Many2one('hr.department', string='Department', related='participant_id.department_id')
    attendance = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Attendance')
    value = fields.Float('Result', default=0)


class HRTraining(models.Model):
    _inherit = 'hr.training'

    note_ids = fields.One2many('training.note', 'training_id', string='Note')
    note_count = fields.Integer('Note Count', compute='_compute_note_count', store=True)
    @api.depends('note_ids')
    def _compute_note_count(self):
        for record in self:
            record.note_count = len(record.note_ids)

    def action_show_note(self):
        self.ensure_one()
        if self.note_count == 0:
            return
        action = self.env.ref('training_note.training_note_action').read()[0]
        action['domain'] = [('id', 'in', self.note_ids.ids)]
        return action

    def generate_training_note(self):
        self.ensure_one()
        self.env['training.note'].create({
            'training_id': self.id,
            'result_ids': [(0,0,{
                'training_id': self.id,
                'participant_id': user.id,
            }) for user in self.participant_ids]
        })

