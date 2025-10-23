from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class GenerateSequenceWizard(models.TransientModel):
    _name = 'generate.sequence.wizard'
    _description = 'Generate Sequence for Department'

    department_id = fields.Many2one('hr.department', string='Department')
    model_id = fields.Many2one('ir.model', string='Model', required=True)
    prefix = fields.Char('Prefix')
    suffix = fields.Char('Suffix')
    padding = fields.Integer('Sequence Size', default=5)
    use_date_range = fields.Boolean('Use subsequences per date_range')
    range_reset = fields.Selection([
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ], string="Range Reset")


    def button_process(self):
        self.ensure_one()

        department = self.department_id
        alias = department.alias
        model = self.model_id

        if not department or not model:
            raise ValidationError("Can't Generate Sequence! Please Contact Administrator!")

        sequence = self.env['ir.sequence'].create({
            'name': model.name + ' for ' + department.name,
            'department_id': department.id,
            'prefix': self.prefix,
            'suffix': self.suffix,
            'padding': self.padding,
            'implementation': 'standard',
            'number_increment': 1,
            'number_next_actual': 1,
            'code': model.model + '.' + alias.lower(),
            'use_date_range': self.use_date_range,
            'range_reset': self.range_reset,
        })
        department.write({ 'sequence_ids': [(0,0, {
            'model_id': model.id,
            'department_id': department.id,
            'sequence_id': sequence.id,
        })] })

