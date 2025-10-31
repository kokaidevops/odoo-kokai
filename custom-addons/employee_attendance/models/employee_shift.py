from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    day_period = fields.Selection(selection_add=[
        ('evening', 'Evening'),
        ('night', 'Night'),
    ], ondelete={'evening': 'cascade', 'night': 'cascade'})


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    employee_shift_ids = fields.Many2many('hr.employee.shift', string='Employee Shift')


class EmployeeShiftSchedule(models.Model):
    _name = 'employee.shift.schedule'
    _description = 'Employee Shift Schedule'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name', copy=False)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user.id, required=True, copy=True)
    department_id = fields.Many2one('hr.department', string='Department', default=lambda self: self.env.user.department_id.id, required=True, copy=True)
    line_ids = fields.One2many('shift.schedule.line', 'schedule_id', string='Line', copy=True)
    allocation_ids = fields.One2many('employee.shift.allocation', 'schedule_id', string='Allocation', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True, copy=False)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('employee.shift.schedule')
        return super().create(vals)

    def action_draft(self):
        self.write({ 'state': 'draft' })

    def action_done(self):
        self._generate_shift_allocation()
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.write({ 'state': 'cancel' })

    def _prepare_shift_allocation_data(self, line, date, employee_id, department_id):
        return {
            'schedule_id': self.id,
            'schedule_line_id': line.id,
            'employee_id': employee_id,
            'date': date,
            'employee_shift_id': line.employee_shift_id.id,
            'department_id': department_id,
            'work_location_id': line.work_location_id.id,
            'note': line.note,
            'state': 'done',
        }

    def _generate_shift_allocation(self):
        for line in self.line_ids:
            current_date = line.date
            end_date = line.end_date
            while current_date <= end_date:
                for employee in line.employee_ids:
                    data = self._prepare_shift_allocation_data(line, current_date, employee.id, employee.department_id.id)
                    self.env['employee.shift.allocation'].create(data)
                current_date += timedelta(days=1)


class ShiftScheduleLine(models.Model):
    _name = 'shift.schedule.line'
    _description = 'Shift Schedule Line'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name', compute='_compute_name', store=True)
    schedule_id = fields.Many2one('employee.shift.schedule', string='Schedule', ondelete='cascade', required=True)
    date = fields.Date('Date', default=fields.Date.today(), required=True)
    end_date = fields.Date('End Date', default=fields.Date.today(), required=True)
    employee_shift_id = fields.Many2one('hr.employee.shift', string='Shift', required=True)
    department_id = fields.Many2one('hr.department', string='Department', related='schedule_id.department_id')
    employee_ids = fields.Many2many('hr.employee', string='Employee', domain="[('department_id', '=', department_id)]", required=True)
    work_location_id = fields.Many2one('hr.work.location', string='Work Location')
    note = fields.Char('Note')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True, copy=False, related='schedule_id.state', store=True)

    @api.onchange('date')
    def _onchange_date(self):
        for record in self:
            record.end_date = record.date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        for record in self:
            if record.end_date < record.date:
                raise ValidationError("End Date can't be less than Start Date")

    @api.depends('date', 'employee_shift_id')
    def _compute_name(self):
        for record in self:
            record.name = '%s[%s]' % (record.date.strftime("%d %b %Y"), record.employee_shift_id.day_period.capitalize())


class EmployeeShiftAllocation(models.Model):
    _name = 'employee.shift.allocation'
    _description = 'Employee Shift Allocation'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    schedule_id = fields.Many2one('employee.shift.schedule', string='Schedule', ondelete='cascade')
    schedule_line_id = fields.Many2one('shift.schedule.line', string='Schedule Line', ondelete='cascade')
    name = fields.Char('Name', compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id.id, required=True)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', default=lambda self: self.env.user.department_id.id, store=True)
    date = fields.Date('Date', default=fields.Date.today(), required=True)
    employee_shift_id = fields.Many2one('hr.employee.shift', string='Employee Shift', required=True)
    work_location_id = fields.Many2one('hr.work.location', string='Work Location')
    note = fields.Text('Note')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('request_exchange', 'Request Exchange'),
        ('exchange', 'Exchange'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True)
    color = fields.Integer('Color', related='employee_shift_id.color')
    specific_readonly_field = fields.Boolean('Specific Readonly Field', compute='_compute_specific_readonly_field')
    is_exchange = fields.Boolean('Is Exchange?')
    parent_id = fields.Many2one('employee.shift.allocation', string='Parent')
    shift_change_id = fields.Many2one('employee.shift.change', string='Employee Shift Change')

    def _compute_specific_readonly_field(self):
        for record in self:
            record.specific_readonly_field = not self.env.user.has_group("employee_attendance.group_employee_shift_allocation_manager")

    @api.depends('employee_id', 'date', 'employee_shift_id')
    def _compute_name(self):
        for record in self:
            day_period = record.employee_shift_id.day_period.capitalize() if record.employee_shift_id.day_period else ""
            record.name = '%s - %s[%s]' % (record.employee_id.name, record.date.strftime("%d %b %Y"), day_period)

    def action_draft(self):
        self.write({ 'state': 'draft' })

    def action_done(self):
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.write({ 'state': 'cancel' })

    def request_shift_change(self):
        ctx = dict(default_shift_allocation_id=self.id, active_ids=self.ids)
        return {
            'name': _('Employee Shift Change'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'employee.shift.replaced.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def unlink(self):
        if not self.state == 'cancel':
            raise ValidationError("Can't delete shift not in Cancel state!")
        return super().unlink()


class EmployeeShiftChange(models.Model):
    _name = 'employee.shift.change'
    _description = 'Employee Shift Change'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    name = fields.Char('Name', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', related='user_id.employee_id')
    department_id = fields.Many2one('hr.department', string='Department', related='user_id.department_id', store=True)
    shift_allocation_id = fields.Many2one('employee.shift.allocation', string='Allocation', required=True, ondelete='cascade')
    init_employee_shift_id = fields.Many2one('hr.employee.shift', string='Init Employee Shift', related='shift_allocation_id.employee_shift_id', store=True)
    init_date = fields.Date('Init Date', related='shift_allocation_id.date', store=True)
    exchange_shift_allocation_id = fields.Many2one('employee.shift.allocation', string='Exchange Shift Allocation')
    employee_shift_id = fields.Many2one('hr.employee.shift', string='Change To')
    date = fields.Date('Change Date', default=lambda self: self.shift_allocation_id.date)
    description = fields.Text('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True)
    approval_ids = fields.One2many('approval.request', 'shift_change_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)
    type = fields.Selection([
        ('change', 'Change'),
        ('replace', 'Replace'),
        ('exchange', 'Exchange'),
    ], string='Type', default='replace', required=True)
    exchange_ids = fields.One2many('employee.shift.allocation', 'shift_change_id', string='Exchange')
    exchange_count = fields.Integer('Exchange Count', compute='_compute_exchange_count', store=True)

    @api.depends('exchange_ids')
    def _compute_exchange_count(self):
        for record in self:
            record.exchange_count = len(record.exchange_ids)

    @api.depends('employee_id')
    def _compute_name(self):
        for record in self:
            date_string = record.init_date.strftime("%d %b %Y") if record.init_date else ""
            record.name = "Request Shift Change - %s [%s]" % (date_string, record.employee_id.name)

    def generate_approval_request(self):
        self.ensure_one()
        approved_request = self.approval_ids.filtered(lambda approval: approval.request_status == 'approved')
        if approved_request:
            raise ValidationError("This Document has been Approved! Can't request approval again!")
        try:
            category_pr = self.env.company.approval_shift_change_id
            vals = {
                'name': 'Request Approval for ' + self.name,
                'shift_change_id': self.id,
                'request_owner_id': self.user_id.id,
                'category_id': category_pr.id,
                'reason': f"Request Approval for {self.name} from {self.user_id.name} \n {self.description or ''}"
            }
            request = self.env['approval.request'].sudo().create(vals)
            query = f"""
UPDATE approval_approver SET user_id={self.employee_id.department_id.manager_id.user_id.id} WHERE request_id={request.id} AND user_id=2;
UPDATE approval_approver SET user_id={self.employee_id.department_id.pic_id.id} WHERE request_id={request.id} AND user_id=175;
                    """
            self.env.cr.execute(query)
            request.action_confirm()
        except Exception as e:
            raise ValidationError("Can't Request Approval. Please Contact Administrator. \n%s" % str(e))

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def action_view_approval_request(self):
        self.ensure_one()
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        action['domain'] = [('id', 'in', approvals.ids)]
        return action

    def action_draft(self):
        self.write({ 'state': 'draft' })

    def action_request(self):
        self.generate_approval_request()
        self.write({ 'state': 'request' })

    def action_approved(self):
        self.action_generate_allocation()
        self.shift_allocation_id.write({ 'state': 'exchange' })
        self.write({ 'state': 'approved' })

    def action_rejected(self, reason):
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('employee_attendance.model_employee_shift_change').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'rejected' })

    def action_cancel(self):
        self.mapped('approval_ids').action_cancel()
        self.write({ 'state': 'cancel' })

    def action_generate_allocation(self):
        if self.exchange_count > 0:
            raise ValidationError("Exchange allocation has been Generated!")
        if self.type == 'replace':
            self.env['employee.shift.allocation'].create({
                'schedule_id': self.shift_allocation_id.schedule_id.id,
                'schedule_line_id': self.shift_allocation_id.schedule_line_id.id,
                'employee_id': self.employee_id.id,
                'department_id': self.employee_id.department_id.id,
                'date': self.date if self.type == 'change' else self.init_date,
                'employee_shift_id': self.employee_shift_id.id,
                'work_location_id': self.shift_allocation_id.work_location_id.id,
                'note': 'Employee Shift Change',
                'state': 'done',
                'parent_id': self.shift_allocation_id.id,
                'is_exchange': True,
                'shift_change_id': self.id,
            })
        if self.type == 'exchange':
            self.env['employee.shift.allocation'].create({
                'schedule_id': self.exchange_shift_allocation_id.schedule_id.id,
                'schedule_line_id': self.exchange_shift_allocation_id.schedule_line_id.id,
                'employee_id': self.shift_allocation_id.employee_id.id,
                'department_id': self.shift_allocation_id.employee_id.department_id.id,
                'date': self.init_date,
                'employee_shift_id': self.exchange_shift_allocation_id.employee_shift_id.id,
                'work_location_id': self.exchange_shift_allocation_id.work_location_id.id,
                'note': 'Employee Shift Change',
                'state': 'done',
                'parent_id': self.exchange_shift_allocation_id.id,
                'is_exchange': True,
                'shift_change_id': self.id,
            })
            self.exchange_shift_allocation_id.write({ 'state': 'exchange' })