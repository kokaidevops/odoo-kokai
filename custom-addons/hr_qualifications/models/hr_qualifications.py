from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HRQualificationType(models.Model):
    _name = 'hr.qualification.type'
    _description = 'HR Qualification Type'
    _order = 'sequence DESC'

    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    level_ids = fields.One2many('hr.qualification.level', 'type_id', string='Level')

    def _set_default_level(self):
        if self.env.context.get('no_qualification_level_check'):
            return
        for types in self:
            if not types.level_ids.filtered('default_level'):
                types.level_ids[:1].default_level = True


class HRQualificationLevel(models.Model):
    _name = 'hr.qualification.level'
    _description = 'Hr Qualification Level'
    _order = 'sequence DESC'

    sequence = fields.Integer('Sequence', default=10)
    type_id = fields.Many2one('hr.qualification.type', string='Qualification Type')
    name = fields.Char('Name')
    description = fields.Char('Description')
    default_level = fields.Boolean('Default Level')

    @api.model_create_multi
    def create(self, vals_list):
        levels = super().create(vals_list)
        levels.type_id._set_default_level()
        return levels

    def write(self, values):
        levels = super().write(values)
        self.type_id._set_default_level()
        return levels

    def unlink(self):
        types = self.type_id
        res = super().unlink()
        types._set_default_level()
        return res

    @api.constrains('default_level', 'type_id')
    def _constrains_default_level(self):
        for type in set(self.mapped('type_id')):
            if len(type.level_ids.filtered('default_level')) > 1:
                raise ValidationError(_('Only one default level is allowed per qualification type.'))

    def action_set_default(self):
        self.ensure_one()
        self.type_id.level_ids.with_context(no_qualification_level_check=True).default_level = False
        self.default_level = True


class HRQualificationLine(models.Model):
    _name = 'hr.qualification.line'

    job_id = fields.Many2one('hr.job', string='Job Position')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    type_id = fields.Many2one('hr.qualification.type', string='Qualification Type')
    level_id = fields.Many2one('hr.qualification.level', string='Level', domain="[('type_id', '=', type_id)]")
    description = fields.Char('Description', related='level_id.description', readonly=False, store=True)


class HRJob(models.Model):
    _inherit = 'hr.job'

    qualification_line_ids = fields.One2many('hr.qualification.line', 'job_id', string='Qualification Line')


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    qualification_line_ids = fields.One2many('hr.qualification.line', 'employee_id', string='Qualification Line')
