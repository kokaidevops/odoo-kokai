from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class StageLostWizard(models.TransientModel):
    _name = 'stage.lost.wizard'

    ref_id = fields.Many2one('crm.lead', string='Reference', required=True)
    reason = fields.Text('Reason', default='-')

    def button_process(self):
        try:
            # TODO check condition for lost stage
            lead = self.ref_id
            lead.change_stage(self.env.ref('crm_management.crm_stage_data_lost_deal').id, self.reason)
            lead.mapped('order_ids').action_cancel()
        except:
            raise ValidationError("Can't set lead to Lost Stage!")