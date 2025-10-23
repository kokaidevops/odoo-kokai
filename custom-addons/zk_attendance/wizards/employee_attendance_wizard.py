from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, timedelta
from ..controllers import main as c

import json
import logging

_logger = logging.getLogger(__name__)


class EmployeeAttendanceWizard(models.TransientModel):
    _name = 'employee.attendance.wizard'
    _description = 'Employee Attendance Wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    get_by = fields.Selection([
        ('all', 'All'),
        ('department', 'Department'),
        ('employee', 'Employee'),
    ], string='Get By', required=True, default='all')
    department_ids = fields.Many2many('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    device_id = fields.Many2one('fingerprint.device', string='Device', required=True)

    def action_sync(self):
        self.ensure_one()

        if not self.device_id:
            raise ValidationError("Choose Fingerprint Device to connect!")
        
        attendances = c.DeviceUsers.get_attendance(self.device_id)
        for attendance in attendances:
            pin = attendance[0]
            punch = attendance[2]
            attendance_date = attendance[1].date()
            if attendance_date < self.start_date or attendance_date > self.end_date or punch == 1:
                continue
            fingerprint = self.env['hr.employee.fingerprint'].search([
                ('pin', '=', int(pin)),
                ('device_id', '=', self.device_id.id),
            ], limit=1)
            if not fingerprint:
                continue
            
            display_name = '[%s] Attendance / %s' % (fingerprint.employee_id.name, attendance_date)
            data = {
                'employee_id': fingerprint.employee_id.id,
                'date': attendance_date,
                'check_in': attendance[1], #datetime.strptime(attendance[1], '%Y-%m-%d %H:%M:%S')
                'work_entry_type_id': self.env.ref('hr_work_entry.work_entry_type_attendance').id,
                'description': display_name,
                'name': display_name,
                'device_id': self.device_id.id,
            }
            _logger.warning(data)
            self.env['hr.attendance'].create(data)
        return True


    def action_confirm(self):
        self.ensure_one()
        data = {}
        data['start_date'] = self.start_date
        data['end_date'] = self.end_date
        data['attendances'] = {}

        if not self.device_id:
            raise ValidationError("Choose Fingerprint Device to connect!")

        attendances = c.DeviceUsers.get_attendance(self.device_id)
        for attendance in attendances:
            user_id = attendance[0]
            if user_id in ["221", '389']:
                continue

            employee_name = user_id
            department = ""

            fingerprint = self.env['hr.employee.fingerprint'].search([
                ('pin', '=', user_id),
                ('device_id', '=', self.device_id.id)
            ], limit=1)
            if not fingerprint:
                continue
            employee_name = fingerprint.employee_id.name
            department = fingerprint.employee_id.department_id.name
            display_name = f"{department} - {employee_name}"

            attendance_date = attendance[1].date()
            punch = attendance[2]

            if attendance_date < self.start_date or attendance_date > self.end_date:
                continue

            if not display_name in data['attendances']:
                data['attendances'][display_name] = [employee_name, department, {}]

            if not attendance_date.strftime('%Y-%m-%d') in data['attendances'][display_name][2]:
                data['attendances'][display_name][2][attendance_date.strftime('%Y-%m-%d')] = []

            data['attendances'][display_name][2][attendance_date.strftime('%Y-%m-%d')].append([attendance[1], punch])
        sorted_attendances = dict(sorted(data["attendances"].items()))
        data["attendances"] = sorted_attendances

        # if (not self.env.user.company_id.logo):
        #     raise UserError(_("You have to set a logo or a layout for your company."))
        # elif (not self.env.user.company_id.external_report_layout_id):
        #     raise UserError(_("You have to set your reports's header and footer layout."))

        return self.env.ref('zk_attendance.action_report_employee_attendance_xlsx').report_action(self, data=data)