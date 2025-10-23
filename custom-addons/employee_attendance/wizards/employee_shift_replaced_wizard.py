from odoo import _, api, fields, models


class EmployeeShiftReplacedWizard(models.TransientModel):
    _name = 'employee.shift.replaced.wizard'
    _description = 'Employee Shift Replaced Wizard'

    shift_allocation_id = fields.Many2one('employee.shift.allocation', string='Shift Allocation', required=True)
    employee_allocation_id = fields.Many2one('hr.employee', string='Owner Allocation', related='shift_allocation_id.employee_id')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id.id)
    exchange_shift_allocation_id = fields.Many2one('employee.shift.allocation', string='Exchange Shift Allocation')
    type = fields.Selection([
        ('replace', 'Replace'),
        ('exchange', 'Exchange'),
    ], string='Type', default='replace', required=True)
    description = fields.Text('Description')
    specific_readonly_field = fields.Boolean('Specific Readonly Field', compute='_compute_specific_readonly_field')

    def _compute_specific_readonly_field(self):
        for record in self:
            record.specific_readonly_field = not self.env.user.has_group("employee_attendance.group_employee_shift_allocation_manager")

    def action_confirm(self):
        shift_change = self.env['employee.shift.change'].create({
            'user_id': self.employee_id.user_id.id,
            'shift_allocation_id': self.shift_allocation_id.id,
            'employee_shift_id': self.shift_allocation_id.employee_shift_id.id,
            'description': self.description,
            'type': self.type,
            'exchange_shift_allocation_id': self.exchange_shift_allocation_id.id,
        })
        shift_change.action_request()
        self.shift_allocation_id.write({ 'state': 'request_exchange' })
        return {
            'name': 'Employee Shift Change',
            'type': 'ir.actions.act_window',
            'res_model': 'employee.shift.change',
            'view_mode': 'form',
            'res_id': shift_change.id,
            'target': 'current',
        }