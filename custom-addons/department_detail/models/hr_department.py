from odoo import _, api, fields, models
from odoo.exceptions import UserError

class IRSequenceDepartment(models.Model):
    _name = 'ir.sequence.department'
    _description = 'Sequence for Each Department'

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    sequence_id = fields.Many2one('ir.sequence', string='Sequence', required=True)

class IRSequence(models.Model):
    _inherit = 'ir.sequence'

    department_id = fields.Many2one('hr.department', string='Department')

class HRDepartment(models.Model):
    _inherit = 'hr.department'

    sequence_ids = fields.One2many('ir.sequence.department', 'department_id', string='Sequence')
    alias = fields.Char('Alias')
    pic_id = fields.Many2one('res.users', string='PIC')
    department_function = fields.Text(string='Functions', help="Description of the department's functions")
    department_task = fields.Text(string='Tasks', help="Description of the department's tasks")
    
    def action_generate_sequence_wizard(self):
        if not self.alias:
            raise UserError('Please Set Alias for Department First!')
        
        ctx = dict(default_department_id=self.id, active_ids=self.ids)
        return {
            'name': _('Generate Sequence'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'generate.sequence.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    @api.onchange('manager_id')
    def _onchange_manager_id(self):
        for record in self:
            record.pic_id = record.manager_id.id