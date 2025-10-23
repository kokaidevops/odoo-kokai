import math
import pytz
import pandas as pd
from dateutil import relativedelta
from datetime import datetime, date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import logging


_logger = logging.getLogger(__name__)


OVERTIME_STATUS = [
    ('draft', 'Draft'),
    ('requested', 'Requested'),
    ('approved', 'Approved'),
    ('refused', 'Refused'),
    ('cancel', 'Cancel'),
]


class HrOvertimeBatch(models.Model):
    _name = 'hr.overtime.batch'
    _description = 'Hr Overtime Batch'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user.id, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', related='user_id.department_id', tracking=True)

    name = fields.Char('Name')
    employee_ids = fields.Many2many('hr.employee', string='Employee', domain="[('department_id', '=', department_id)]", tracking=True)
    total_employee = fields.Integer('Total Employee', compute='_compute_total_employee', store=True)
    accept_employee = fields.Integer('Accept Employee', tracking=True)
    line_ids = fields.One2many('overtime.batch.line', 'batch_id', string='Line', tracking=True)
    overtime_ids = fields.One2many('hr.overtime', 'batch_id', string='Overtime')
    state = fields.Selection(OVERTIME_STATUS, string='Status', default='draft', tracking=True)
    note = fields.Text('Note', tracking=True)
    approval_ids = fields.One2many('approval.request', 'hr_overtime_batch_id', string='Approval', tracking=True)
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('hr.overtime.batch')
        return super(HrOvertimeBatch, self).create(vals)

    @api.onchange('total_employee')
    def _onchange_total_employee(self):
        for record in self:
            if record.state == 'approved':
                return
            record.accept_employee = record.total_employee

    @api.depends('employee_ids')
    def _compute_total_employee(self):
        for record in self:
            record.total_employee = len(record.employee_ids)

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def action_show_approval(self):
        if self.approval_count == 0:
            return
        action = self.env.ref('approvals.approval_request_action_all').read()[0]
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    def action_draft(self):
        self.write({ 'state': 'draft' })
        self.line_ids.action_draft()

    def action_requested(self):
        category_pr = self.env.company.approval_overtime_batch_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'hr_overtime_batch_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for Overtime {self.name} by {self.user_id.name}"
        }
        request = self.env['approval.request'].create(vals)
        request.action_confirm()
        self.write({ 
            'state': 'requested',
            'accept_employee': self.total_employee,
        })

    def action_approved(self):
        self.write({ 'state': 'approved' })
        self.line_ids.action_approved()

    def action_refused(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('hr_overtime.model_hr_overtime_batch').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'refused' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    def _prepare_overtime_data(self, employee, schedule):
        self.ensure_one()
        user_tz = pytz.timezone(self.env.context.get('tz'))

        date_start = schedule.start_time
        hours_start = int(date_start)
        minutes_start = math.ceil((date_start%1)*60)
        combine_time_start = f"{hours_start}:{minutes_start}:00"
        combine_datetime_start = user_tz.localize(datetime.combine(schedule.date, datetime.strptime(combine_time_start, "%H:%M:%S").time()), is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)

        date_end = schedule.end_time
        hours_end = int(date_end)
        minutes_end = math.ceil((date_end%1)*60)
        combine_time_end = f"{hours_end}:{minutes_end}:00"
        combine_datetime_end = user_tz.localize(datetime.combine(schedule.date_end, datetime.strptime(combine_time_end, "%H:%M:%S").time()), is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)

        return {
            'company_id': self.company_id.id,
            'user_id': employee.user_id.id,
            'batch_id': self.id,
            'date': schedule.date,
            # 'date_from': schedule.date_from,
            # 'date_to': schedule.date_to,
            'date_from': combine_datetime_start,
            'date_to': combine_datetime_end,
            'description': schedule.reason,
            'state': 'approved',
            'overtime_type_id': schedule.overtime_type_id.id,
            'request_unit': schedule.request_unit,
            'request_date_from_period': schedule.request_date_from_period,
            'actual_hours': schedule.actual_hours,
            'batch_line_id': schedule.id,
        }

    def generate_overtime(self):
        self.ensure_one()
        if not self.accept_employee == self.total_employee:
            raise ValidationError("Employees submitted and approved are different, please correct them first!")
        for line in self.line_ids:
            if not line.state == 'approved':
                continue
            if not line.overtime_type_id:
                raise ValidationError("Set Overtime Type first! Please contact administrator!")
            for employee in self.employee_ids:
                data = self._prepare_overtime_data(employee, line)
                overtime = self.env['hr.overtime'].create(data)
                # overtime.generate_attendance()

    def _repair_data(self):
        for line in self.line_ids:
            line.write({
                'date_end': line.date,
            })


class OvertimeBatchLine(models.Model):
    _name = 'overtime.batch.line'
    _description = 'Overtime Batch Line'

    name = fields.Char('Name', compute='_compute_name')
    batch_id = fields.Many2one('hr.overtime.batch', string='Batch')
    date = fields.Date('Start Date', default=fields.Date.today())
    date_end = fields.Date('End Date', default=fields.Date.today())
    request_unit = fields.Selection([
        ('full', 'Full Day'),
        ('half', 'Half Day'),
        ('hour', 'Hours'),
    ], string='Request Unit', default='hour', required=True)
    request_date_from_period = fields.Selection([
        ('am', 'Morning'),
        ('pm', 'Afternoon'),
    ], string='Request Date FRom Period', default='am', required=True)
    start_time = fields.Float('Start Time', default=18.0)
    end_time = fields.Float('End Time', default=19.0)
    hours = fields.Float('Hours', compute='_compute_hours', store=True)
    actual_hours = fields.Float('Actual Hours', related='hours', store=True, readonly=False)
    reason = fields.Char('Reason')
    overtime_type_id = fields.Many2one('overtime.type', string='Overtime Type', default=lambda self: self.env['overtime.type'].search([], limit=1, order='sequence ASC, id ASC').id)
    state = fields.Selection(OVERTIME_STATUS, string='Status', default='draft', tracking=True, required=True, compute='_compute_state', store=True)

    @api.depends('date', 'start_time', 'end_time')
    def _compute_name(self):
        for record in self:
            record.name = "%s/%s [%s - %s]" %(record.batch_id.department_id.name, record.date, record.start_time, record.end_time)

    @api.depends('start_time', 'end_time', 'request_unit')
    def _compute_hours(self):
        for record in self:
            hours = 0
            if record.request_unit == 'full':
                hours = 8
            elif record.request_unit == 'half':
                hours = 4
            if record.request_unit == 'hour':
                hours = record.end_time - record.start_time
                # start_dt = fields.Datetime.from_string(record.date_from)
                # finish_dt = fields.Datetime.from_string(record.date_to)
                # difference = relativedelta.relativedelta(finish_dt, start_dt)
                # hours = difference.days*24 + difference.hours
            record.hours = hours

    def action_refused(self):
        self.write({ 'state':'refused' })

    def action_approved(self):
        if self.state in ['refused', 'cancel']:
            return
        self.write({ 'state':'approved' })

    def action_cancel(self):
        self.write({ 'state':'cancel' })

    def action_draft(self):
        self.write({ 'state':'cancel' })

    @api.depends('batch_id.state')
    def _compute_state(self):
        for record in self:
            if record.state == record.batch_id.state:
                record.state = record.batch_id.state


class HROvertime(models.Model):
    _name = 'hr.overtime'
    _description = 'HR Overtime'
    _inherit = ['mail.activity.mixin', 'mail.thread']

    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)

    batch_id = fields.Many2one('hr.overtime.batch', string='Batch')
    batch_line_id = fields.Many2one('overtime.batch.line', string='Batch Line')
    name = fields.Char('Name', default='Overtime Request')
    employee_id = fields.Many2one('hr.employee', string='Employee', related='user_id.employee_id')
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager", related="employee_id.parent_id.user_id", store=True)
    contract_id = fields.Many2one('hr.contract', string="Contract", related="employee_id.contract_id")
    overtime_type_id = fields.Many2one('overtime.type')
    date = fields.Date('Date', compute='_compute_date', store=True)
    date_from = fields.Datetime('Start Date', default=fields.Datetime.now())
    date_to = fields.Datetime('End Date')
    request_unit = fields.Selection([
        ('full', 'Full Day'),
        ('half', 'Half Day'),
        ('hour', 'Hours'),
    ], string='Request Unit', default='hour', required=True)
    request_date_from_period = fields.Selection([
        ('am', 'Morning'),
        ('pm', 'Afternoon'),
    ], string='Request Date FRom Period', default='am', required=True)
    days_no_tmp = fields.Float('Hours', compute="_get_days", store=True)
    actual_hours = fields.Float('Actual Hours', related='days_no_tmp', store=True, readonly=False)
    description = fields.Text('Reason')
    state = fields.Selection(OVERTIME_STATUS, string='Status', default='draft', tracking=True)
    leave_id = fields.Many2one('hr.leave.allocation', string="Leave ID")
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.One2many('hr.attendance', 'overtime_id', string='Attendance')
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    approval_ids = fields.One2many('approval.request', 'hr_overtime_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count', store=True)
    overtime_cost = fields.Float('Overtime Cost')

    @api.depends('date_from')
    def _compute_date(self):
        for recd in self:
            recd.date = recd.date_from.date()

    @api.depends('date_from', 'date_to', 'request_unit')
    def _get_days(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError('Start Date must be less than End Date')
        for sheet in self:
            hours = 0
            if sheet.request_unit == 'full':
                hours = 8
            if sheet.request_unit == 'half':
                hours = 4
            if sheet.date_from and sheet.date_to and sheet.request_unit == 'hour':
                start_dt = fields.Datetime.from_string(sheet.date_from)
                finish_dt = fields.Datetime.from_string(sheet.date_to)
                difference = relativedelta.relativedelta(finish_dt, start_dt)
                hours = difference.days*24 + difference.hours
            sheet.update({ 'days_no_tmp': hours })

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
        category_pr = self.env.company.approval_overtime_id
        vals = {
            'name': 'Request Approval for ' + self.name,
            'hr_overtime_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for Overtime {self.name} for {self.user_id.name} from {self.date_from} to {self.date_to}"
        }
        request = self.env['approval.request'].create(vals)
        query = f"UPDATE approval_approver SET user_id={self.employee_id.parent_id.user_id.id} WHERE request_id={request.id} AND user_id=2"
        self.env.cr.execute(query)
        request.action_confirm()
        self.write({ 'state': 'requested' })

    def action_approved(self):
        self.ensure_one()
        # TODO needed send notification to User?
        self.write({ 'state': 'approved' })
        self.generate_attendance()

    def action_refused(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('hr_overtime.model_hr_overtime').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'refused' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for req in self:
            domain = [
                ('date_from', '<=', req.date_to),
                ('date_to', '>=', req.date_from),
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', 'not in', ['refused']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_('%s can not have 2 Overtime requests that overlaps on same day!' % (req.employee_id.name)))

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('hr.overtime')
        return super(HROvertime, self).create(vals)

    def unlink(self):
        for overtime in self.filtered(lambda overtime: overtime.state != 'draft'):
            raise UserError(_('You cannot delete TIL request which is not in draft state.'))
        return super(HROvertime, self).unlink()

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_date(self):
        holiday = False
        if self.contract_id and self.date_from and self.date_to:
            for leaves in self.contract_id.resource_calendar_id.global_leave_ids:
                leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
                overtime_dates = pd.date_range(self.date_from, self.date_to).date
                for over_time in overtime_dates:
                    for leave_date in leave_dates:
                        if leave_date == over_time:
                            holiday = True
            if holiday:
                self.write({'public_holiday': 'You have Public Holidays in your Overtime request.'})
            else:
                self.write({'public_holiday': ' '})
            hr_attendance = self.env['hr.attendance'].search([
                ('check_in', '>=', self.date_from),
                ('check_in', '<=', self.date_to),
                ('employee_id', '=', self.employee_id.id)
            ])
            self.update({ 'attendance_ids': [(6, 0, hr_attendance.ids)] })

    def _compute_overtime_cost(self, contract=False):
        if not contract:
            raise ValidationError("Contract not Found!")
        for record in self:
            overtime_cost = 0
            if contract.have_overtime_package or record.overtime_type_id.type == 'leave' or record.state != 'approved':
                record.overtime_cost = overtime_cost
                return
            if record.request_unit == 'full':
                record.overtime_cost = contract.over_day
                return
            if record.request_unit == 'half':
                record.overtime_cost = contract.over_day*0.5
                return
            for line in record.overtime_type_id.rule_line_ids:
                if line.to_hrs <= record.actual_hours:
                    overtime_cost += line.hrs_amount*line.range
                elif line.from_hrs < record.actual_hours:
                    overtime_cost += line.hrs_amount*(record.actual_hours-line.from_hrs)
                else:
                    break
            record.overtime_cost = overtime_cost*contract.over_hour

    def _prepare_attendance_data(self):
        self.ensure_one()
        return {
            'check_in': self.date_from,
            'check_out': self.date_to,
            'company_id': self.company_id.id,
            'date': self.date,
            'employee_id': self.employee_id.id,
            'source': 'overtime',
            'work_entry_type_id': self.env.ref('hr_payroll_attendance.overtime_work_entry_type').id,
            'overtime_id': self.id,
        }

    def generate_attendance(self):
        self.ensure_one()
        data = self._prepare_attendance_data()
        self.env['hr.attendance'].create(data)


class HrOverTimeType(models.Model):
    _name = 'overtime.type'
    _description = "HR Overtime Type"
    _order = 'sequence ASC, id ASC'

    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    type = fields.Selection([
        ('cash', 'Cash'),
        ('leave', 'Leave ')
    ], string="Type", default='cash')
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type', domain="[('id', 'in', leave_compute)]")
    leave_compute = fields.Many2many('hr.leave.type', compute="_get_leave_type")
    rule_line_ids = fields.One2many('overtime.type.rule', 'type_line_id')
    description = fields.Text('Description')

    def _get_leave_type(self):
        ids = []
        leave_type = self.env['hr.leave.type'].search([('request_unit', '=', 'hour')])
        for recd in leave_type:
            ids.append(recd.id)
        self.leave_compute = ids


class HrOverTimeTypeRule(models.Model):
    _name = 'overtime.type.rule'
    _description = "HR Overtime Type Rule"

    type_line_id = fields.Many2one('overtime.type', string='Over Time Type')
    name = fields.Char('Name', required=True)
    from_hrs = fields.Float('From', required=True)
    to_hrs = fields.Float('To', required=True)
    range = fields.Float('Range', compute='_compute_range', store=True)
    hrs_amount = fields.Float('Rate', required=True)

    @api.depends('from_hrs', 'to_hrs')
    def _compute_range(self):
        for record in self:
            record.range = record.to_hrs - record.from_hrs


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    hr_overtime_ids = fields.One2many('hr.overtime', 'employee_id', string='Overtime')
    overtime_count = fields.Integer('Overtime Count', compute='_compute_overtime_count', store=True)
    @api.depends('hr_overtime_ids')
    def _compute_overtime_count(self):
        for record in self:
            record.overtime_count = len(record.hr_overtime_ids)

    def action_show_overtime(self):
        self.ensure_one()
        action = self.env.ref('hr_overtime.hr_overtime_action').read()[0]
        action['domain'] = [('id', 'in', self.hr_overtime_ids.ids)]
        return action


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    overtime_count = fields.Integer('Overtime Count', related='employee_id.overtime_count')