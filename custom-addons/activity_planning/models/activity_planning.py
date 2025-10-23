from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime, time
import logging


_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    planning_ids = fields.One2many('planning.slot', 'activity_id', string='Planning')

    def _prepare_planning_values(self):
        document = self.env[self.res_model_id.model].browse(self.res_id)
        document_name = document.display_name if document else ''
        return {
            'activity_id': self.id,
            'resource_id': self.user_id.employee_id.resource_id.id,
            'start_datetime': datetime.combine(self.start_date, time(1,0,0)),
            # 'start_datetime': datetime.combine(self.create_date.date(), time(1,0,0)),
            'repeat': False,
            'end_datetime': datetime.combine(self.date_deadline, time(10,0,0)),
            'res_model_id': self.res_model_id.id,
            'res_id': self.res_id,
            'name': "%s: %s" % (document_name, self.summary or ''),
        }

    def _generate_planning(self):
        self.ensure_one()
        data = self._prepare_planning_values()
        planning = self.env['planning.slot'].sudo().create(data)
        planning.action_publish()
    
    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for record in res:
            record._generate_planning()
        return res

    def unlink(self):
        _logger.warning("activity unlink")
        for record in self:
            record.mapped('planning_ids').unlink()
        res = super().unlink()
        return res
    
    def action_feedback(self, feedback=False, attachment_ids=None):
        self.mapped('planning_ids').action_done()
        res = super().action_feedback(feedback, attachment_ids)
        return res


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    res_model_id = fields.Integer('Res Model ID')
    res_id = fields.Integer('Res ID')
    activity_id = fields.Many2one('mail.activity', string='Activity', ondelete='set null')
    state = fields.Selection(selection_add=[ 
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], ondelete={ 
        'done': 'cascade',
        'cancel': 'cascade',
    })
    timesheet_ids = fields.One2many('account.analytic.line', 'planning_id', string='Timesheet')
    timesheet_id = fields.Many2one('account.analytic.line', string='Current Timesheet', compute='_compute_timesheet_id')

    @api.depends('timesheet_ids', 'timesheet_ids.running')
    def _compute_timesheet_id(self):
        for record in self:
            for timesheet in self.timesheet_ids.filtered(lambda timesheet: timesheet.running):
                record.timesheet_id = timesheet.id

    def _prepare_timesheet_values(self):
        return {
            'planning_id': self.id,
            'name': self.name,
            'start_date': fields.Datetime.now(),
            'date': fields.Date.today(),
        }

    def _generate_timesheet(self):
        if self.timesheet_id:
            raise ValidationError("Can't running two timesheet at same time!")
        data = self._prepare_timesheet_values()
        timesheet = self.env['account.analytic.line'].create(data)
        return timesheet

    def start_timesheet(self):
        timesheet = self._generate_timesheet()
        timesheet.action_start_timer()

    def stop_timesheet(self):
        self.timesheet_id.action_end_timer()
    
    def action_done(self):
        self.write({ 'state': 'done' })
    
    def action_cancel(self):
        if not self.state == 'done':
            self.write({ 'state': 'cancel' })

    def unlink(self):
        if not self.state == 'done':
            return super().unlink()


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    planning_id = fields.Many2one('planning.slot', string='Planning')