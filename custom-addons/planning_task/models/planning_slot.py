from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TaskInstruction(models.Model):
    _name = 'task.instruction'
    _description = 'Task Instruction'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _order = 'sequence ASC, id ASC'

    planning_id = fields.Many2one('planning.slot', string='Planning')
    activity_id = fields.Many2one('department.activity', string='Activity')
    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name')
    title = fields.Char('Title')
    note = fields.Html('Note')


class PlanningSlot(models.Model):
    _name = 'planning.slot'
    _inherit = ['mail.activity.mixin', 'mail.thread', 'planning.slot']

    activity_id = fields.Many2one('department.activity', string='Activity')
    instruction_ids = fields.One2many('task.instruction', 'planning_id', string='Instruction')
    instruction_count = fields.Integer('Instruction Count', compute='_compute_instruction_count')
    area_id = fields.Many2one('hr.work.area', string='Area')
    timesheet_ids = fields.One2many('account.analytic.line', 'planning_id', string='timesheet')
    allocated_hours = fields.Float(compute='_compute_timesheet_allocated', store=True, readonly=True)
    responsible_id = fields.Many2one('res.users', string='Responsible')
    state = fields.Selection(selection_add=[
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], ondelete={
        'progress': 'cascade',
        'done': 'cascade',
        'cancel': 'cascade',
    })
    has_running = fields.Boolean('Has Running?', compute='_compute_has_running_timesheet', store=True, readonly=True)

    @api.depends('timesheet_ids', 'timesheet_ids.running')
    def _compute_has_running_timesheet(self):
        for record in self:
            record.has_running = len(self.timesheet_ids.filtered(lambda timesheet: timesheet.running)) > 0

    @api.depends('timesheet_ids')
    def _compute_timesheet_allocated(self):
        for record in self:
            record.allocated_hours = sum([timesheet.unit_amount for timesheet in record.timesheet_ids])

    @api.depends('instruction_ids')
    def _compute_instruction_count(self):
        for record in self:
            record.instruction_count = len(record.instruction_ids)

    def _prepare_timesheet_value(self):
        self.ensure_one()
        return {
            'start_date': fields.Datetime.now(),
            'date': fields.Date.today(),
            'name': f"{self.activity_id.name}\n\n{self.name}",
            'user_id': self.user_id.id,
            'project_id': self.activity_id.project_id.id,
            'running': True,
        }

    def _get_timesheet_running(self):
        self.ensure_one()
        timesheets = self.timesheet_ids.filtered(lambda timesheet: timesheet.running)
        return timesheets

    def _stop_timesheet(self):
        self.ensure_one()
        timesheets = self._get_timesheet_running()
        for timesheet in timesheets:
            timesheet.action_end_timer()

    def action_start(self):
        self.ensure_one()
        timesheet_running = self._get_timesheet_running()
        if len(timesheet_running) > 0:
            raise ValidationError("Can't start timesheet while there is a timesheet still running!")
        val = self._prepare_timesheet_value()
        self.env['account.analytic.line'].create(val)
        self.write({ 'state': 'progress' })
    
    def action_pause(self):
        self.ensure_one()
        self._stop_timesheet()

    def action_done(self):
        self.ensure_one()
        self._stop_timesheet()
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    planning_id = fields.Many2one('planning.slot', string='Planning')