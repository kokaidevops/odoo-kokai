from odoo import _, api, fields, models, modules, tools
from odoo.exceptions import UserError
from ..controllers import main as c
import os, json, logging, pytz
from datetime import datetime, timezone


_logger = logging.getLogger(__name__)


class FingerprintDevice(models.Model):
    _name = 'fingerprint.device'
    _description = 'Fingerprint Device'

    name = fields.Char('Device Name')
    ip_address = fields.Char('IP Address')
    port = fields.Integer('Port', default=4370)
    sequence = fields.Integer('Sequence')
    device_password = fields.Char('Device Password', default=0)
    state = fields.Selection([
        ('0', 'Active'),
        ('1', 'Inactive')
    ], string='State', default='1')
    difference = fields.Float('Time Difference with UTC', default=0)

    def test_connection(self):
        try:
            with c.ConnectToDevice(self.ip_address, self.port, self.device_password) as conn:
                if conn:
                    self.write({ 'state': '0' })
        except:
            self.write({ 'state': '1' })
            raise UserError("Can't reach Fingerprint Device")

    def get_attendance(self):
        ctx = dict(default_device_id=self.id, active_ids=self.ids)
        return {
            'name': _('Employee Attendance'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'employee.attendance.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def import_attendance_from_json(self):
        self.ensure_one()
        module_path = modules.get_module_path('zk_attendance')
        json_file_path = os.path.join(module_path, 'models', 'processed_data.json')
        data = {}
        try:
            with tools.file_open(json_file_path, 'r') as f:
                attendances = json.load(f)
                for attendance in attendances:
                    fingerprint = attendance['fingerprint']
                    date_from_data = attendance['date']
                    
                    check_in = datetime.strptime("%s+07:00" % attendance['check_in'], '%Y-%m-%d %H:%M:%S%z')
                    check_in  = check_in.astimezone(timezone.utc)
                    check_in = check_in.replace(tzinfo=None)
                    check_out = datetime.strptime("%s+07:00" % attendance['check_out'], '%Y-%m-%d %H:%M:%S%z')
                    check_out  = check_out.astimezone(timezone.utc)
                    check_out = check_out.replace(tzinfo=None)

                    fingerprint = self.env['hr.employee.fingerprint'].search([
                        ('pin', '=', fingerprint),
                        ('device_id', '=', self.id)
                    ], limit=1)
                    if not fingerprint:
                        continue
                    employee_name = fingerprint.employee_id.name
                    data = {
                        'check_in': check_in,
                        'check_out': check_out,
                        'date': date_from_data,
                        'device_id': self.id,
                        'source': 'fingerprint',
                        #### processed data in server
                        'employee_id': fingerprint.employee_id.id,
                        'description': '%s - [%s]' % (employee_name, date_from_data),
                        'state': 'draft',
                        'work_entry_type_id': self.env.ref('hr_work_entry.work_entry_type_attendance').id,
                    }
                    try:
                        self.env['hr.attendance'].create(data)
                    except Exception as e:
                        _logger.warning(e)
                _logger.warning("import done")
        except FileNotFoundError:
            _logger.warning(f"Error: JSON file not found at {json_file_path}")
        except json.JSONDecodeError:
            _logger.warning(f"Error: Invalid JSON format in {json_file_path}")

    def process_data_from_fingerprint(self):
        ctx = dict(default_device_id=self.id, active_ids=self.ids)
        return {
            'name': _('Process Data'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'device.extract.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }