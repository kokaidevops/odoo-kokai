from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import pytz
from datetime import timedelta, datetime, date, time
import logging


_logger = logging.getLogger(__name__)


class GenerateCompleteAttendanceWizard(models.TransientModel):
    _name = 'generate.complete.attendance.wizard'
    _description = 'Generate Complete Attendance Wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    employee_type = fields.Selection([
        ('all', 'All'),
        ('monthly', 'Monthly Wage'),
        ('hourly', 'Hourly Wage'),
        ('select', 'Select'),
    ], string='Employee Type', default='monthly', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employee')

    def generate_check_date(self, user_tz, date, shift_time):
        convert_time = time(int(shift_time), int((shift_time-int(shift_time))*60), 0)
        return user_tz.localize(datetime.combine(date, convert_time), is_dst=None).astimezone(pytz.utc).replace(tzinfo=None)

    def datetime_to_localize(self, user_tz, datetime_string):
        return pytz.utc.localize(datetime_string, is_dst=None).astimezone(user_tz).replace(tzinfo=None)

    def action_generate(self):
        user_tz_string = self.env.user.tz or self.env.context.get('tz')
        user_tz = pytz.timezone(user_tz_string)
        start_date = self.start_date
        end_date = self.end_date
        current_date = start_date
        
        domain = [
            ('active', '=', True),
            ('skip_complete_attendance', '=', False),
        ]
        if self.employee_type in ['monthly', 'hourly']:
            domain.append(('contract_id.wage_type', '=', self.employee_type))
        if self.employee_type == 'select':
            domain.append(('id', 'in', self.employee_ids.ids))

        employees = self.env['hr.employee'].search(domain)
        employee_ids = []
        employee_data = {}
        for employee in employees:
            employee_ids.append(employee.id)
            employee_data[employee.id] = employee
        employee_ids_filter = ",".join(str(item) for item in employee_ids)

        while current_date <= end_date:
            complete_attendance_ids = []
            half_attendance_ids = []
            query = """
SELECT employee_id, COUNT(employee_id) AS total, counted_unit
FROM hr_attendance
WHERE employee_id IN (%s) AND (date<='%s' AND date_out>='%s')
GROUP BY employee_id, counted_unit
            """ % (employee_ids_filter, current_date.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d"))
            self.env.cr.execute(query)
            datas = self.env.cr.fetchall()
            # complete_attendance_ids = [data[0] for data in datas]
            for data in datas:
                if int(data[1]) == 1 and data[2] == 'half':
                    half_attendance_ids.append(data[0])
                else:
                    complete_attendance_ids.append(data[0])
            missing_attendance_ids = set(employee_ids) - set(complete_attendance_ids)
            for employee_id in missing_attendance_ids:
                employee = employee_data[employee_id]
                if current_date < employee.service_start_date or (employee.contract_id.date_end and employee.contract_id.date_end < current_date):
                    continue
                working_day = self.env['resource.calendar.attendance'].search([
                    ('dayofweek', '=', current_date.weekday()),
                    ('calendar_id', '=', employee.contract_id.resource_calendar_id.id),
                ])
                if not working_day:
                    continue
                public_holiday = self.env['resource.calendar.leaves'].search([
                    ('date', '=', current_date),
                    ('holiday', '=', True),
                ], limit=1)
                if public_holiday:
                    continue
                data = {
                    'employee_id': employee_id,
                    'check_in': self.generate_check_date(user_tz, current_date, employee.employee_shift_id.start_time),
                    'check_out': self.generate_check_date(user_tz, current_date, employee.employee_shift_id.end_time),
                    'name': 'Complete Attendance',
                    'counted_unit': 'full',
                    'source': 'default',
                    'work_entry_type_id': self.env.ref('hr_work_entry.work_entry_type_attendance').id,
                }
                _logger.warning(data)
                self.env['hr.attendance'].create(data)
#             for employee_id in half_attendance_ids:
#                 query = """
# SELECT employee_id, check_in, check_out 
# FROM hr_attendance
# WHERE employee_id=%s AND (date<='%s' AND date_out>='%s')
#                 """ % (employee_id, current_date.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d"))
#                 self.env.cr.execute(query)
#                 attendance = self.env.cr.fetchone()
#                 if attendance:
#                     check_in = self.datetime_to_localize(user_tz, attendance[1])
#                     check_out = self.datetime_to_localize(user_tz, attendance[2])
#                     data = {
#                         'employee_id': employee_id,
#                         'check_in': self.generate_check_date(user_tz, current_date, employee.employee_shift_id.start_time),
#                         'check_out': self.generate_check_date(user_tz, current_date, employee.employee_shift_id.end_time),
#                         'name': 'Complete Attendance',
#                         'counted_unit': 'half',
#                         'source': 'default',
#                         'work_entry_type_id': self.env.ref('hr_work_entry.work_entry_type_attendance').id,
#                     }
#                     _logger.warning(data)
#                     self.env['hr.attendance'].create(data)
            current_date += timedelta(days=1)