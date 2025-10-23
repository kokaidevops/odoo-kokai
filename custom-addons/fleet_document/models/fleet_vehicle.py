from odoo import _, api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    document_ids = fields.One2many('base.document', 'fleet_id', string='Document')
    document_count = fields.Integer('Document Count', compute='_compute_document_count', store=True)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    def action_show_document(self):
        action = self.env.ref('document_expiry.base_document_action').sudo().read()[0]
        action['domain'] = [('id', 'in', self.document_ids.ids)]
        return action