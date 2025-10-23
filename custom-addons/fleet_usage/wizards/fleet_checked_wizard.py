from odoo import _, api, fields, models

STATE_POSITION = {
    'parking': 'out',
    'out': 'come',
}


class FleetCheckedWizard(models.TransientModel):
    _name = 'fleet.checked.wizard'
    _description = 'Fleet Checked Wizard'

    usage_id = fields.Many2one('fleet.usage', string='Usage')
    equipment_id = fields.Many2one('fleet.equipment.usage', string='Equipment')
    condition_id = fields.Many2one('fleet.condition.usage', string='Condition')
    remark = fields.Char('Remark')

    def action_submit(self):
        self.ensure_one()
        self.env['fleet.checked'].create({
            'equipment_id': self.equipment_id.id,
            'condition_id': self.condition_id.id,
            'user_id': self.env.user.id,
            'remark': self.remark,
            'state': STATE_POSITION[self.usage_id.position],
            'condition': 'bad',
        })