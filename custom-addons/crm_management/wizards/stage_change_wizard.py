from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class StageChangeWizard(models.TransientModel):
    _name = 'stage.change.wizard'

    ref_id = fields.Many2one('crm.lead', string='Reference', required=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', required=True)
    reason = fields.Text('Reason', default='-')

    def button_process(self):
        self.ensure_one()
        
        if self.ref_id and self.stage_id:
            lead = self.ref_id

            lead.change_stage(self.stage_id.id, self.reason)
            
            # if self.stage_id.is_lost:
            #     for order in self.ref_id.order_ids:
            #         order._action_cancel()
        else:
            raise ValidationError("Change Stage can't be Processed!")