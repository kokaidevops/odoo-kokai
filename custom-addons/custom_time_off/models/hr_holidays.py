from collections import defaultdict
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
import logging
import math
import pytz


_logger = logging.getLogger(__name__)


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    range = fields.Float('Range', default=1)
    range_type = fields.Selection([
        ('day', 'Days'),
        ('month', 'Months'),
        ('year', 'Years'),
    ], string='Range Type', default='month', required=True)
    duration = fields.Float('Duration')
    leave_validation_type = fields.Selection(selection_add=[ ('custom', 'Custom') ], ondelete={ 'custom': 'cascade' })
    custom_approval = fields.Boolean('Custom Approval')
    can_payout = fields.Boolean('Can Payout?')
    create_work_entry = fields.Boolean('Create Work Entry?')
    create_attendance = fields.Boolean('Create Attendance?')
    actual_allocation = fields.Float('Actual Allocation', compute='_compute_actual_allocation', search='_search_actual_allocation')

    def _search_actual_allocation(self, operator, value):
        value = float(value)
        employee_id = self._get_contextual_employee_id()
        leaves = defaultdict(int)

        if employee_id:
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee_id),
                ('state', '=', 'validate')
            ])
            for allocation in allocations:
                leaves[allocation.holiday_status_id.id] += allocation.actual_allocation
        valid_leave = []
        for leave in leaves:
            if operator == '>':
                if leaves[leave] > value:
                    valid_leave.append(leave)
            elif operator == '<':
                if leaves[leave] < value:
                    valid_leave.append(leave)
            elif operator == '=':
                if leaves[leave] == value:
                    valid_leave.append(leave)
            elif operator == '!=':
                if leaves[leave] != value:
                    valid_leave.append(leave)
        return [('id', 'in', valid_leave)]

    @api.depends_context('employee_id', 'default_employee_id')
    def _compute_actual_allocation(self):
        employee_id = self._get_contextual_employee_id()
        employee_ids = employee_id if isinstance(employee_id, list) else [employee_id]
        for holiday_status in self:
            allocations = self.env['hr.leave.allocation'].with_context(active_test=False).search([
                ('employee_id', 'in', employee_ids),
                ('state', 'in', ['validate']),
                ('holiday_status_id', '=', holiday_status.id),
            ])
            actual_allocation = 0
            for allocation in allocations:
                actual_allocation += allocation.actual_allocation
            holiday_status.actual_allocation = actual_allocation

    def name_get(self):
        _logger.warning(self._context.get('holiday_status_name_custom', False))
        if not self._context.get('holiday_status_name_custom', False):
            return super().name_get()
        res = []
        for record in self:
            name = record.name
            if record.requires_allocation == "yes" and not self._context.get('from_manager_leave_form'):
                name = "%(name)s (%(count)s)" % {
                    'name': name,
                    'count': _('%g remaining out of %g') % (
                        float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
                        float_round(record.actual_allocation, precision_digits=2) or 0.0,
                    ) + (_(' hours') if record.request_unit == 'hour' else _(' days'))
                }
            res.append((record.id, name))
        return res


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    source = fields.Selection(selection_add=[ ('time_off', 'Time Off') ], ondelete={ 'time_off': 'cascade' })
    leave_id = fields.Many2one('hr.leave', string='Time Off')


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.depends_context('uid')
    @api.depends('state', 'employee_id')
    def _compute_can_cancel(self):
        res = super()._compute_can_cancel()
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        return res or is_manager

    @api.model_create_multi
    def create(self, vals):
        holidays = super(HrLeave, self).create(vals)
        for holiday in holidays:
            if holiday.holiday_status_id.custom_approval:
                query = "UPDATE hr_leave SET state='draft' WHERE id=%s" % holiday.id
                self.env.cr.execute(query)
        return holidays

    attendance_id = fields.Many2one('hr.attendance', string='Attendance')
    approval_ids = fields.One2many('approval.request', 'leave_id', string='Approval Request')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count')
    payslip_state = fields.Selection(default='done')
    actual_days = fields.Float('Actual Days', compute='_compute_number_of_days', store=True, readonly=False)

    def _compute_number_of_days(self):
        res = super()._compute_number_of_days()
        for holiday in self:
            holiday.actual_days = holiday.number_of_days
        return res

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def generate_approval_request(self):
        try:
            self.ensure_one()
            category_pr = self.env.company.approval_time_off_id
            vals = {
                'name': 'Request Approval for %s' % self.display_name,
                'leave_id': self.id,
                'request_owner_id': self.employee_id.user_id.id,
                'category_id': category_pr.id,
                'reason': f"Request Approval for {self.name} from {self.employee_id.name} \n {self.name}",
                'approver_id': self.env.user.id,
            }
            
            request = self.env['approval.request'].sudo().create(vals)
            # query = f"UPDATE approval_approver SET user_id={self.employee_id.user_id.department_id.manager_id.user_id.id} WHERE request_id={request.id} AND user_id=2 RETURNING id"
            # self.env.cr.execute(query)
            # updated_id = self.env.cr.fetchone()
            # query = "DELETE FROM approval_approver WHERE id!=%s AND user_id=%s AND request_id=%s" % (updated_id[0], self.employee_id.user_id.department_id.manager_id.user_id.id, request.id)
            # self.env.cr.execute(query)
            request.action_confirm()
        except Exception as e:
            raise ValidationError("Can't Request Approval. Please Contact Administrator. %s" % e)

    def action_show_approval(self):
        self.ensure_one()
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        approvals = self.mapped('approval_ids')
        if self.approval_count == 0:
            return
        elif self.approval_count > 1:
            action['domain'] = [('id', 'in', approvals.ids)]
        elif approvals:
            action['views'] = [(self.env.ref('approvals.approval_request_view_form').id, 'form')]
            action['res_id'] = approvals.ids[0]
        return action

    def action_confirm(self):
        res = super(HrLeave, self).action_confirm()
        if self.holiday_status_id.custom_approval:
            self.generate_approval_request()
        return res

    def action_validate(self):
        if self.holiday_status_id.custom_approval:
            return
        return super().action_validate()

    def action_draft(self):
        res = super().action_draft()
        for approval in self.approval_ids:
            approval.action_cancel()
        return res

    def _prepare_work_entry_data(self, current_date, working_hour):
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
            'work_entry_type_id': self.holiday_status_id.work_entry_type_id.id,
            'date_start': combine_datetime_start,
            'date_stop': combine_datetime_end,
            'state': 'validated',
            'name': "%s - %s" % (self.employee_id.name, self.holiday_status_id.name),
            'leave_id': self.id,
        }

    def generate_work_entry(self):
        self.ensure_one()
        work_entries = self.env['hr.work.entry'].search([ ('leave_id', '=', self.id) ])
        if work_entries or not self.holiday_status_id.create_work_entry:
            return
        current_date = self.date_from
        while current_date <= self.date_to:
            domain = [
                ('dayofweek', '=', current_date.weekday()),
                ('calendar_id', '=', self.employee_id.contract_id.resource_calendar_id.id),
            ]
            if self.request_unit_half:
                day_period = 'afternoon' if self.request_date_from_period == 'pm' else 'morning'
                domain.append(('day_period', '=', day_period))
            working_hours = self.env['resource.calendar.attendance'].search(domain, order='hour_from ASC')
            for line in working_hours:
                data = self._prepare_work_entry_data(current_date, line)
                self.env['hr.work.entry'].create(data)
            current_date += timedelta(days=1)

    def _generate_attendance(self):
        self.ensure_one()
        return {
            'source': 'time_off',
            'leave_id': self.id,
        }

    @api.depends('holiday_status_id', 'holiday_status_id.requires_allocation', 'validation_type', 'employee_id', 'date_from', 'date_to')
    def _compute_from_holiday_status_id(self):
        res = super()._compute_from_holiday_status_id()
        for holiday in self:
            allocation = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', holiday.employee_id.id),
                ('holiday_status_id', '=', holiday.holiday_status_id.id),
                ('state', '=', 'validate'),
            ], limit=1)
            if allocation:
                holiday.write({ 'holiday_allocation_id': allocation.id })
        return res
    
    def generate_holiday_allocation_id(self):
        allocation = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.employee_id.id),
            ('holiday_status_id', '=', self.holiday_status_id.id),
            ('state', '=', 'validate'),
        ], limit=1)
        if allocation:
            self.write({ 'holiday_allocation_id': allocation.id })

    def _prepare_attendance_data(self):
        return {
            'name': self.name,
            'user_id': self.employee_id.user_id.id,
            'employee_id': self.employee_id.id,
            'check_in': self.date_from,
            'check_out': self.date_to,
            'counted_unit': 'full',
            'source': 'time_off',
            'description': '%s - [Time Off]' % (self.employee_id.name, ),
            'working_schedule_id': '',
            'work_entry_type_id': self.holiday_status_id.work_entry_type_id.id,
            'state': 'validate',
            'leave_id': self.id
        }

    def _generate_attendance(self):
        attendance = self.env['hr.attendance'].search([ ('leave_id', '=', self.id) ])
        if attendance or not self.holiday_status_id.create_attendance:
            return
        if self.number_of_days < 1:
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', self.employee_id.id),
                ('date', '=', self.date_from.date()),
            ])
            if self.request_date_from_period == 'am' and self.date_from.time().hour == 1:
                attendance.write({
                    'check_in_init': attendance.check_in,
                    'check_in': self.date_to,
                })
            if self.request_date_from_period == 'pm' and self.date_to.time().hour == 10:
                attendance.write({
                    'check_out_init': attendance.check_out,
                    'check_out': self.date_from,
                })
        data = self._prepare_attendance_data()
        self.env['hr.attendance'].create(data)

    def action_custom_validate(self):
        self.write({ 'state': 'validate' })

    def action_refuse(self, reason):
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('hr_holidays.model_hr_leave').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        return super().action_refuse()

    def _action_user_cancel(self, reason):
        if self.holiday_status_id.custom_approval:
            self._force_cancel(reason, 'mail.mt_note')
            return
        return super()._action_user_cancel(reason)


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    state = fields.Selection(selection_add=[ ('expired', 'Expired') ], ondelete={ 'expired': 'cascade' })
    actual_allocation = fields.Float('Actual Duration')
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    allocation_usage = fields.Integer('Allocation Usage', compute='_compute_allocation_usage', store=True)

    backdate_time_off = fields.Boolean('Backdate TIme Off')
    backdate_usage = fields.Float('Backdate Usage')

    remaining_days = fields.Float('Remaining Duration', compute='_compute_remaining_days', store=True)

    @api.depends('taken_leave_ids', 'taken_leave_ids.state', 'taken_leave_ids.number_of_days', 'taken_leave_ids.actual_days')
    def _compute_allocation_usage(self):
        for record in self:
            taken_leave_ids = record.taken_leave_ids.filtered(lambda leave: leave.state == 'validate')
            # record.allocation_usage = sum([leave.number_of_days for leave in taken_leave_ids])
            record.allocation_usage = sum([leave.actual_days for leave in taken_leave_ids])

    @api.depends('backdate_time_off', 'backdate_usage', 'allocation_usage', 'number_of_days')
    def _compute_remaining_days(self):
        for record in self:
            usage_days = record.backdate_usage if record.backdate_time_off else record.allocation_usage
            record.remaining_days = record.actual_allocation - usage_days

    def _prepare_time_off(self, to_data={}):
        leave_type = self.env['hr.leave.type'].search([ ('id', '=', to_data['type_id']) ], limit=1)
        if not leave_type:
            raise ValidationError("Time Off Type not Found!")
        if leave_type.range <= 0:
            raise ValidationError("Range can't be set to 0!")

        today = fields.Date.today()
        today = to_data['service_start_date'].replace(year=today.year)
        date_to = today
        if leave_type.range_type == 'day':
            date_to = today + relativedelta(days=(leave_type.range-1))
        if leave_type.range_type == 'month':
            date_to = today + relativedelta(months=leave_type.range, days=-1)
        if leave_type.range_type == 'year':
            date_to = today + relativedelta(years=leave_type.range, days=-1)

        query_allocation_usage = """
SELECT SUM(allocation_usage)
FROM hr_leave_allocation 
WHERE employee_id=%s AND holiday_status_id=%s 
        """  % (to_data['employee_id'], to_data['type_id'])
        self.env.cr.execute(query_allocation_usage)
        data_allocation_usage = self.env.cr.fetchone()
        allocation_usage = data_allocation_usage[0] if data_allocation_usage else 0

        duration = leave_type.duration
        contract = self.env['hr.contract'].search([allocation_usage
            ('employee_id', '=', to_data['employee_id']),
            ('state', '=', 'open'),
        ], limit=1)
        if contract.wage_type == 'hourly':
            duration = 0
            date_one_year_ago = today - relativedelta(years=1)
            query = """
SELECT 
COALESCE(COUNT(CASE WHEN counted_unit='half' THEN 1 END)*0.5, 0) + COALESCE(COUNT(CASE WHEN counted_unit='full' THEN 1 END), 0) AS total_attendance
FROM hr_attendance
WHERE employee_id=%s AND work_entry_type_id=%s AND date>=%s AND date<=%s
            """ % (to_data['employee_id'], self.env.ref('hr_work_entry.work_entry_type_attendance').id, date_one_year_ago, today)
            self.env.cr.execute(query)
            data = self.env.cr.fetchone()
            if data:
                duration = round(data[0]/21)
        return {
            'name': to_data['name'],
            'holiday_status_id': to_data['type_id'],
            'allocation_type': 'regular',
            'date_from': today,
            'date_to': date_to,
            'holiday_type': 'employee',
            'employee_id': to_data['employee_id'],
            'number_of_days': duration+allocation_usage,
            'actual_allocation': duration,
        }

    @api.model
    def _cron_generate_time_off(self, to_data):
        query_active_emp = """
            SELECT hr_employee.id, hr_employee.name, hr_employee.service_duration_years, hr_employee.service_start_date 
            FROM hr_employee 
            WHERE hr_employee.active=True AND hr_employee.id != 1
        """
        self.env.cr.execute(query_active_emp)
        employees = self.env.cr.fetchall()
        for employee in employees:
            if not employee[3] or (to_data['type_id'] == self.env.ref('hr_holidays.holiday_status_cl').id and int(employee[2]) <= 0):
                continue
            query_hr_leave_allocation = """
                SELECT id, employee_id, holiday_status_id, state
                FROM hr_leave_allocation 
                WHERE employee_id=%s AND holiday_status_id=%s 
                ORDER BY date_from DESC, id DESC
            """ % (employee[0], to_data['type_id'])
            self.env.cr.execute(query_hr_leave_allocation)
            exist_allocation = self.env.cr.fetchone()
            if (not exist_allocation) or (exist_allocation and exist_allocation[3] == 'expired'):
                to_data['employee_id'] = employee[0]
                to_data['service_start_date'] = employee[3]
                data = self._prepare_time_off(to_data)
                allocation = self.env['hr.leave.allocation'].create(data)
                allocation.action_confirm()
        return True
        
    @api.model
    def _update_state_expired(self):
        query = """
            UPDATE hr_leave_allocation SET state='expired'
            WHERE state='validate' AND date_to<='%s'
        """ % (fields.Date.today())
        self.env.cr.execute(query)
        return True