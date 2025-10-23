from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    fingerprint_ids = fields.One2many('hr.employee.fingerprint', 'employee_id', string='Fingerprint')


class HrEmployeeFingerprint(models.Model):
    _name = 'hr.employee.fingerprint'
    _description = 'Hr Employee Fingerprint'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    device_id = fields.Many2one('fingerprint.device', string='Device')
    pin = fields.Char('PIN')


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    source = fields.Selection(selection_add=[ ('fingerprint', 'Fingerprint') ], ondelete={ 'fingerprint': 'cascade' })
    device_id = fields.Many2one('fingerprint.device', string='Device')

    def _attendance_to_work_entry(self, source):
        res = super()._attendance_to_work_entry(source)
        return res or source == 'fingerprint'