from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class SafetyInduction(models.Model):
    _name = 'safety.induction'
    _description = 'Safety Induction'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users', string='User')
    speaker_id = fields.Many2one('res.users', string='PIC', default=lambda self: self.env.user.id)
    name = fields.Char('Name', default='New')
    date = fields.Datetime('Date', default=fields.Datetime.now())
    location_id = fields.Many2one('hr.work.location', string='Location')
    area_id = fields.Many2one('hr.work.area', string='Area', domain="[('location_id', '=', location_id)]")
    type = fields.Selection([
        ('new', 'New Employee'),
        ('visitor', 'Visitor'),
    ], string='Type', default='new', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', related='user_id.employee_id')
    partner_id = fields.Many2one('res.partner', string='Partner')
    line_ids = fields.One2many('safety.induction.line', 'induction_id', string='Line')
    emergency_name = fields.Char('Contact Name')
    emergency_address = fields.Text('Address')
    emergency_relationship = fields.Char('Relationship')
    emergency_number = fields.Char('Phone Number')
    statement = fields.Text('Statement', default='''
Saya dengan ini menyatakan bahwa saya telah mengikuti Induction Keselamatan, Kesehatan Kerja dan Lingkungan. Dan berjanji mengikuti petunjuk yang diberikan dan semua Aturan Keselamatan yang berlaku di project ini.\n
Saya menyatakan bahwa informasi yang diberikan adalah benar dan tepat 
''')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('need_improvement', 'Need Improvement'),
        ('cancel', 'Cancel'),
    ], string='State', required=True, default='draft')
    approval_ids = fields.One2many('approval.request', 'induction_id', string='approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_ids', store=True)

    @api.depends('approval_ids')
    def _compute_approval_ids(self):
        for record in self:
            record.approval_count = len(record.approval_ids)
        
    def action_show_approval(self):
        self.ensure_one()
        if self.approval_count == 0:
            return
        action = self.env.ref('approvals.approval_request_action_all').read()[0]
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if 'name' not in val or val['name'] == 'New':
                val['name'] = self.env['ir.sequence'].next_by_code('safety.induction')
            topics = self.env['induction.topic'].search([ ('active', '=', True) ])
            val['line_ids'] = [(0,0,{
                'topic_id': topic.id,
            }) for topic in topics]
        return super(SafetyInduction, self).create(vals)

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_requested(self):
        self.ensure_one()
        category_pr = self.env.ref('safety_induction.approval_category_data_safety_induction')
        vals = {
            'name': 'Request Approval for ' + self.name,
            'induction_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for {self.name} from {self.speaker_id.name} \n The Induction has been delivered from {self.speaker_id.name}. Please review and approve this report."
        }
        self.sudo().write({ 'approval_ids': [(0, 0, vals)] })
        request = self.approval_ids[len(self.approval_ids)-1]
        request.action_confirm()
        
        # notif to qhse manager
        assignment = self.env['assignment.task'].sudo().create({
            'department_ids': [self.env.company.qhse_manager_id.department_id.id],
            'user_id': self.env.user.id,
            'user_ids': [self.env.company.qhse_manager_id.id],
            'assigned_to': 'employee',
            'subject': f"Laporan Safety Induction",
            'description': f"Berikut laporan mengenai safety induction yang dibawakan oleh {self.speaker_id.name}. \n Terima Kasih.",
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'model': 'safety.induction',
            'res_id': self.id,
        })
        if not assignment:
            raise ValidationError("Can't Assignment Task! Please contact Administrator!")
        
        self.write({ 'state': 'requested' })

    def action_approved(self):
        self.ensure_one()
        self.write({ 'state': 'approved' })

    def action_need_improvement(self):
        self.ensure_one()
        notification = self.env['schedule.task'].sudo().create({
            'company_id': self.env.company.id,
            'subject': 'Notifikasi Refused Safety Induction',
            'user_id': self.speaker_id.id,
            'assign_by_id': 1,
            'schedule_type_id': self.env.ref('schedule_task.mail_activity_type_data_notification').id,
            'description': f"Kepada {self.speaker_id.name} \n The report about safety induction from {self.speaker_id.name} has been refused. Please correct the report based on refused reason report",
            'date': fields.Date.today(),
            'start_date': fields.Datetime.now(),
            'stop_date': fields.Datetime.now(),
            'state': 'draft',
            'type': 'notification',
            'model': 'safety.induction',
            'res_id': self.id,
        })
        notification.action_assign()
        self.write({ 'state': 'need_improvement' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    def action_show_announcement(self):
        self.ensure_one()
        action = self.env.ref('safety_induction.induction_announcement_action').read()[0]
        action['domain'] = [('active', '=', True)]
        return action


class SafetyInductionLine(models.Model):
    _name = 'safety.induction.line'
    _description = 'Safety Induction Line'

    induction_id = fields.Many2one('safety.induction', string='Induction')
    topic_id = fields.Many2one('induction.topic', string='Topic')
    done = fields.Boolean('Done')


class InductionTopic(models.Model):
    _name = 'induction.topic'
    _description = 'Induction Topic'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')


class InductionAnnouncement(models.Model):
    _name = 'induction.announcement'
    _description = 'Induction Announcement'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    description = fields.Text('Description')
