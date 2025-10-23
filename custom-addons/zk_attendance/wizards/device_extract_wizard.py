from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import base64
import json
from datetime import datetime, timezone
import logging


_logger = logging.getLogger(__name__)


class DeviceExtractWizard(models.TransientModel):
    _name = 'device.extract.wizard'
    _description = 'Device Extract Wizard'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    device_id = fields.Many2one('fingerprint.device', string='Device', required=True)
    file = fields.Binary('File', required=True)

    def action_process(self):
        data = {}
        data['start_date'] = self.start_date
        data['end_date'] = self.end_date
        data['attendances'] = {}

        if not self.device_id:
            raise ValidationError("Choose Fingerprint Device to connect!")

        if not self.file:
            raise ValidationError("Please Upload File!")

        decoded_data = base64.b64decode(self.file)
        json_string = decoded_data.decode('utf-8')
        attendances = json.loads(json_string)
        fingerprints = {}
        for attendance in attendances:
            check_in = attendance['check_in']
            check_out = attendance['check_out']
            attendance_date = attendance['date']
            pin = attendance['fingerprint']
            if not pin:
                continue
            employee_name = fingerprints[pin]['employee_name'] if pin in fingerprints else ''
            department_name = fingerprints[pin]['department_name'] if pin in fingerprints else ''
            display_name = fingerprints[pin]['display_name'] if pin in fingerprints else ''

            if not pin in fingerprints:
                emp_fingerprint = self.env['hr.employee.fingerprint'].search([
                    ('pin', '=', pin),
                    ('device_id', '=', self.device_id.id)
                ], limit=1)
                if not emp_fingerprint:
                    continue

                employee_name = emp_fingerprint.employee_id.name
                department_name = emp_fingerprint.employee_id.department_id.name
                display_name = "%s - %s" %(department_name, employee_name)
                fingerprints[pin] = {
                    'employee_name': employee_name,
                    'department_name': department_name,
                    'display_name': display_name
                }

            if not display_name in data['attendances']:
                data['attendances'][display_name] = [employee_name, department_name, {}]

            if not attendance_date in data['attendances'][display_name][2]:
                data['attendances'][display_name][2][attendance_date] = []

            data['attendances'][display_name][2][attendance_date].append([check_in, 0])
            data['attendances'][display_name][2][attendance_date].append([check_out, 1])
        sorted_attendances = dict(sorted(data["attendances"].items()))
        data["attendances"] = sorted_attendances

        return self.env.ref('zk_attendance.action_report_employee_attendance_xlsx').report_action(self, data=data)

    def action_import(self):
        if not self.device_id:
            raise ValidationError("Choose Fingerprint Device to connect!")
        if not self.file:
            raise ValidationError("Please Upload File!")

        decoded_data = base64.b64decode(self.file)
        json_string = decoded_data.decode('utf-8')
        attendances = json.loads(json_string)

        for attendance in attendances:
            attendance_date = attendance['date']
            pin = attendance['fingerprint']
            if not pin:
                continue

            check_in = datetime.strptime("%s+07:00" % attendance['check_in'], '%Y-%m-%d %H:%M:%S%z')
            check_in  = check_in.astimezone(timezone.utc)
            check_in = check_in.replace(tzinfo=None)
            check_out = datetime.strptime("%s+07:00" % attendance['check_out'], '%Y-%m-%d %H:%M:%S%z')
            check_out  = check_out.astimezone(timezone.utc)
            check_out = check_out.replace(tzinfo=None)

            fingerprint = self.env['hr.employee.fingerprint'].search([
                ('pin', '=', pin),
                ('device_id', '=', self.device_id.id)
            ], limit=1)
            if not fingerprint:
                continue
            employee_name = fingerprint.employee_id.name
            data = {
                'check_in': check_in,
                'check_out': check_out,
                'date': attendance_date,
                'device_id': self.device_id.id,
                'source': 'fingerprint',
                #### processed data in server
                'employee_id': fingerprint.employee_id.id,
                'description': '%s - [%s]' % (employee_name, attendance_date),
                'state': 'draft',
                'work_entry_type_id': self.env.ref('hr_work_entry.work_entry_type_attendance').id,
            }
            try:
                self.env['hr.attendance'].create(data)
            except Exception as e:
                _logger.warning(e)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Import Attendance from Fingerprint Device successfully'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }