from odoo import _, api, fields, models
import math
import pytz
from datetime import datetime, timezone, timedelta
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    skip_complete_attendance = fields.Boolean('Skip Complete Attendance?')
    have_shift = fields.Boolean('Have Shift?')


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    color = fields.Integer('Color', related='work_entry_type_id.color', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id')
    name = fields.Char('Name', related='work_entry_type_id.name', store=True)
    date = fields.Date('Date', compute='_compute_date', store=True)
    date_out = fields.Date('Date Out', compute='_compute_date_out', store=True)
    work_entry_type_id = fields.Many2one('hr.work.entry.type', string='Work Entry Type', default=lambda self: self.env.ref('hr_work_entry.work_entry_type_attendance').id)
    working_schedule_id = fields.Many2one('resource.calendar', string='Working Schedule', related='employee_id.contract_id.standard_calendar_id', store=True)
    source = fields.Selection([
        ('default', 'Attendance'),
    ], string='Source', default='default', required=True)
    description = fields.Char('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validated'),
        ('paid', 'Paid'),
        ('cancel', 'Rejected'),
    ], string='State', default='draft', required=True)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batch')
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    counted_unit = fields.Selection([
        ('none', 'None'),
        ('half', 'Half Day'),
        ('full', 'Full Day'),
    ], string='Counted', default='full', required=True, compute='_compute_counted_unit', store=True, readonly=False)

    def _compute_counted_unit(self):
        for record in self:
            if record.worked_hours <= 2:
                record.counted_unit = 'none'
            if record.worked_hours > 2 and record.worked_hours <= 5:
                record.counted_unit = 'half'
            if record.worked_hours > 5:
                record.counted_unit = 'full'

    def _prepare_hr_attendance_penalty(self, time, doc_type='late'):
        return {
            'attendance_id': self.id,
            'time': time,
            'type': doc_type,
        }

    def _attendance_late(self):
        HrAttendancePenalty = self.env['hr.attendance.penalty']
        user_tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
        check_in_time = pytz.utc.localize(self.check_in).astimezone(timezone.utc).astimezone(user_tz).time()
        check_in = check_in_time.hour+check_in_time.minute/60.0
        late_time = check_in - self.employee_id.employee_shift_id.start_time
        if late_time > 0:
            data = self._prepare_hr_attendance_penalty(late_time)
            attendance_late = HrAttendancePenalty.search([
                ('attendance_id', '=', self.id),
                ('type', '=', 'late'),
            ], limit=1)
            if attendance_late:
                attendance_late.write(data)
            else:
                HrAttendancePenalty.create(data)
        else:
            HrAttendancePenalty.sudo().search([('attendance_id', 'in', [self.id])]).write({'active': False})

    def _early_dismissal(self):
        HrAttendancePenalty = self.env['hr.attendance.penalty']
        user_tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
        check_out_time = pytz.utc.localize(self.check_out).astimezone(timezone.utc).astimezone(user_tz).time()
        check_out = check_out_time.hour+check_out_time.minute/60.0
        early_time = self.employee_id.employee_shift_id.end_time - check_out
        _logger.warning(early_time)
        if early_time > 0:
            data = self._prepare_hr_attendance_penalty(early_time, 'early')
            early_dismissal = HrAttendancePenalty.search([
                ('attendance_id', '=', self.id),
                ('type', '=', 'early'),
            ], limit=1)
            if early_dismissal:
                early_dismissal.write(data)
            else:
                HrAttendancePenalty.create(data)
        else:
            HrAttendancePenalty.sudo().search([('attendance_id', 'in', [self.id])]).write({'active': False})

    def _generate_hr_attendance_penalty(self):
        for attendance in self:
            attendance._attendance_late()
            if not attendance.check_out:
                return
            attendance._early_dismissal()

    def generate_hr_attendance_penalty(self):
        self._generate_hr_attendance_penalty()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._generate_hr_attendance_penalty()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._generate_hr_attendance_penalty()
        return res

    def unlink(self):
        self.env['hr.attendance.penalty'].sudo().search([('attendance_id', 'in', self.ids)]).write({'active': False})
        return super().unlink()

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_validate(self):
        self.ensure_one()
        self.write({ 'state': 'validate' })
        self._generate_work_entry()

    def action_paid(self):
        self.ensure_one()
        self.write({ 'state': 'paid' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    @api.depends('check_in')
    def _compute_date(self):
        for record in self:
            user_tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
            check_in = pytz.utc.localize(record.check_in, is_dst=None).astimezone(user_tz).replace(tzinfo=None)
            record.date = check_in.date()
    
    @api.depends('check_out')
    def _compute_date_out(self):
        for record in self:
            user_tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
            check_out = pytz.utc.localize(record.check_out, is_dst=None).astimezone(user_tz).replace(tzinfo=None)
            record.date_out = check_out.date()

    def _work_entry_source_attendance(self):
        return self.employee_id.contract_id.work_entry_source == 'attendance'

    def _attendance_to_work_entry(self, source):
        return source == 'default'

    def _prepare_work_entry_data(self, working_hour, current_date):
        self.ensure_one()
        user_tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
        date_start = working_hour.hour_from
        hours_start = int(date_start)
        minutes_start = math.ceil((date_start%1)*60)
        combine_time_start = f"{hours_start}:{minutes_start}:00"
        combine_datetime_start = user_tz.localize(datetime.combine(current_date, datetime.strptime(combine_time_start, "%H:%M:%S").time()), is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)

        date_end = working_hour.hour_to
        hours_end = int(date_end)
        minutes_end = math.ceil((date_end%1)*60)
        combine_time_end = f"{hours_end}:{minutes_end}:00"
        combine_datetime_end = user_tz.localize(datetime.combine(current_date, datetime.strptime(combine_time_end, "%H:%M:%S").time()), is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)

        return {
            'employee_id': self.employee_id.id,
            'work_entry_type_id': self.work_entry_type_id.id,
            'date_start': combine_datetime_start,
            'date_stop': combine_datetime_end,
            'state': 'validated',
            'name': self.name,
            'attendance_id': self.id,
        }

    def _skip_generate_work_entry(self):
        work_entries = self.env['hr.work.entry'].search([ '|', ('attendance_id', '=', self.id), '&', ('date', '=', self.date), ('employee_id', '=', self.employee_id.id) ])
        if work_entries or (self._work_entry_source_attendance() and not self._attendance_to_work_entry(self.source)) or self.counted_unit == 'none':
            return True
        return False

    def _generate_work_entry(self):
        self.ensure_one()
        user_tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
        # work_entries = self.env['hr.work.entry'].search([ '|', ('attendance_id', '=', self.id), '&', ('date', '=', self.date), ('employee_id', '=', self.employee_id.id) ])
        # if work_entries or (self._work_entry_source_attendance() and not self._attendance_to_work_entry(self.source)) or self.counted_unit == 'none':
        skip = self._skip_generate_work_entry()
        if skip:
            _logger.warning("skip generate_work_entry")
            return
        current_date = self.date
        while current_date <= self.date_out:
            domain = [
                ('dayofweek', '=', current_date.weekday()),
                ('calendar_id', '=', self.working_schedule_id.id),
            ]
            if self.counted_unit == 'half':
                check_in = pytz.utc.localize(self.check_in, is_dst=None).astimezone(user_tz).replace(tzinfo=None)
                check_in = check_in.time().hour+check_in.time().minute/60.0
                _logger.warning(check_in)
                day_period = 'afternoon' if check_in >= 12 else 'morning'
                domain.append(('day_period', '=', day_period))
            working_hours = self.env['resource.calendar.attendance'].search(domain, order='hour_from ASC')
            for line in working_hours:
                data = self._prepare_work_entry_data(line, current_date)
                self.env['hr.work.entry'].create(data)
            current_date += timedelta(days=1)

    def _update_date(self):
        user_tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
        date_in = pytz.utc.localize(self.check_in, is_dst=None).astimezone(user_tz).replace(tzinfo=None)
        date_out = pytz.utc.localize(self.check_out, is_dst=None).astimezone(user_tz).replace(tzinfo=None)
        self.write({
            'date': date_in,
            'date_out': date_out
        })


class HrEmployeeShift(models.Model):
    _name = 'hr.employee.shift'
    _description = 'Hr Employee Shift'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    start_time = fields.Float('Planned Hour', default=8)
    end_time = fields.Float('End Hour', default=17.5)
    day_period = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
    ], string='Day Period', default='morning', required=True)
    color = fields.Integer('Color')

    def name_get(self):
        res = []
        for record in self:
            name = "%s [%s]" % (record.name, record.day_period.capitalize())
            res.append((record.id, name))
        return res


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_shift_id = fields.Many2one('hr.employee.shift', string='Default Employee Shift', ondelete='cascade')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    employee_shift_id = fields.Many2one('hr.employee.shift', string='Default Employee Shift', related='employee_id.employee_shift_id')


class HrAttendancePenalty(models.Model):
    _name = 'hr.attendance.penalty'
    _description = 'Hr Attendance Penalty'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', compute='_compute_name')
    attendance_id = fields.Many2one('hr.attendance', string='Attendance', ondelete='cascade')
    time = fields.Float('Time')
    date = fields.Date('Date', related='attendance_id.date')
    employee_id = fields.Many2one('hr.employee', string='Employee', related='attendance_id.employee_id', store=True)
    penalty_type = fields.Selection([
        ('none', 'None'),
        ('actual', 'Actual Time'),
        ('hour', 'Round Hour'),
        ('half', 'Half Day'),
        ('full', 'Full Day'),
    ], string='Penalty Type', default='half', required=True)
    penalty_amount = fields.Float('Penalty Amount', readonly=True)
    payroll_id = fields.Many2one('hr.payslip', string='Payroll')
    type = fields.Selection([
        ('late', 'Late Attendance'),
        ('early', 'Early Dismissal'),
    ], string='Type', default='late', required=True)
    hard_pass = fields.Boolean('Pass It?')
    hard_penalty = fields.Boolean('Penalty It?')

    @api.depends('attendance_id', 'time', 'employee_id', 'type')
    def _compute_name(self):
        for record in self:
            time = "%02d:%02d" % (int(record.time), round((record.time-int(record.time))*60))
            record.name = "%s - %s: %s" % (record.employee_id.name, dict(record._fields['type'].selection).get(record.type), time)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    attendance_ids = fields.One2many('hr.attendance', 'payslip_run_id', string='Attendance')
    attendance_count = fields.Integer('Attendance Count', compute='_compute_attendance_count')

    @api.depends('attendance_ids')
    def _compute_attendance_count(self):
        for record in self:
            record.attendance_count = len(record.attendance_ids)

    def action_show_attendance(self):
        self.ensure_one()
        action = (self.env.ref('hr_attendance.hr_attendance_action').sudo().read()[0])
        action['context'] = {'search_default_employee': 1}
        action['domain'] = [('id', 'in', self.attendance_ids.ids)]
        return action

    def _update_attendance_in_payslip(self):
        self.ensure_one()
        query = "UPDATE hr_attendance SET payslip_run_id=NULL WHERE payslip_run_id=%s" %(self.id)
        self.env.cr.execute(query)
        query = """
            UPDATE hr_attendance SET payslip_run_id=%s
            WHERE payslip_run_id IS NULL AND date>='%s' AND date<='%s'
        """ % (self.id, self.date_start, self.date_end)
        self.env.cr.execute(query)

    def compute_attendance(self):
        self.ensure_one()
        self._update_attendance_in_payslip()


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    create_attendance = fields.Boolean('Create Attendance')
