from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    location_id = fields.Many2one('hr.work.location', string='Location', tracking=True)
    area_id = fields.Many2one('hr.work.area', string='Area', tracking=True)

    type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Type', required=True, default='internal', tracking=True)
    media = fields.Selection([
        ('meeting', 'Meeting'),
        ('call', 'Call'),
        ('message', 'Message'),
    ], string='Media', required=True, default='meeting', tracking=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Files', tracking=True)
    note_ids = fields.One2many('note.note', 'calendar_id', string='MoM')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assign', 'Assign'),
        ('progress', 'Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', required=True, tracking=True, default='draft')

    attendance_ids = fields.One2many('calendar.event.attendance', 'calendar_id', string='Attendance')

    # participant_type = fields.Selection([
    #     ('all', 'All'),
    #     ('department', 'Department'),
    #     ('employee', 'Employee'),
    # ], string='Participant Type', default='all', tracking=True)
    # department_ids = fields.Many2many('hr.department', string='Department', tracking=True)
    # employee_type_ids = fields.Many2many('hr.contract.type', string='Employee Type', tracking=True)
    # access_share = fields.Selection([
    #     ('all', 'All'),
    #     ('participant', 'Participants Only'),
    # ], string='Access Share', default='participant')

    @api.onchange('area_id')
    def _onchange_area_id(self):
        for record in self:
            record.location = record.area_id.name or ""

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_assign(self):
        self.ensure_one()
        for partner in self.partner_ids:
            if partner.users_id.id:
                self.env['mail.activity'].create({
                    'res_model_id': self.env.ref('calendar.model_calendar_event').id,
                    'res_id': self._origin.id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_meeting').id,
                    'date_deadline': self.start.date(),
                    'user_id': partner.users_id.id,
                    'summary': 'You have been scheduled to attend the following meeting. Please attend the meeting. Thank You!',
                    'batch': self.name,
                    'handle_by': 'all',
                })
        self.write({ 'state': 'assign' })

    def action_progress(self):
        self.ensure_one()
        for partner in self.partner_ids:
            self.env['calendar.event.attendance'].create({
                'calendar_id': self.id,
                'user_id': partner.users_id.id,
                'attend_id': self.env.ref('employee_attendance.attendance_value_data_absent').id,
            })
        self.write({ 'state': 'progress' })

    def action_done(self):
        self.ensure_one()
        query = f"DELETE FROM mail_activity WHERE res_model_id={self.env.ref('calendar.model_calendar_event').id} AND res_id={self._origin.id}"
        self.env.cr.execute(query)
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.ensure_one()
        query = f"DELETE FROM mail_activity WHERE res_model_id={self.env.ref('calendar.model_calendar_event').id} AND res_id={self._origin.id}"
        self.env.cr.execute(query)
        query = f"DELETE FROM calendar_event_attendance WHERE calendar_id={self._origin.id}"
        self.env.cr.execute(query)
        self.write({ 'state': 'cancel' })

    def action_attend(self):
        self.ensure_one()
        self.mapped('attendance_ids').filtered(lambda attendance: attendance.user_id == self.env.user.id).action_attend()


class NoteNote(models.Model):
    _inherit = 'note.note'

    calendar_id = fields.Many2one('calendar.event', string='Calendar', ondelete='cascade')
    date = fields.Datetime('Date', default=fields.Datetime.now(), tracking=True)


class CalendarEventAttendance(models.Model):
    _name = 'calendar.event.attendance'

    calendar_id = fields.Many2one('calendar.event', string='Calendar', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Participant', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    datetime_attend = fields.Datetime('Datetime Attendance', tracking=True)

    def action_attend(self):
        self.ensure_one()
        query = f"DELETE FROM mail_activity WHERE res_model_id={self.env.ref('calendar.model_calendar_event').id} AND res_id={self.calendar_id.id} AND user_id={self.env.user.id}"
        self.env.cr.execute(query)
        self.write({ 'datetime_attend': fields.Datetime.now() })
