# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    documents_vehicle_settings = fields.Boolean(related='company_id.documents_vehicle_settings', readonly=False, string="Document")
    vehicle_folder_id = fields.Many2one('documents.folder', related='company_id.vehicle_folder_id', readonly=False, string="Document default workspace")
    vehicle_tag_ids = fields.Many2many('documents.tag', 'document_tags_rel', related='company_id.vehicle_tag_ids', readonly=False, string="Document Tags")

    @api.onchange('vehicle_folder_id')
    def onchange_document_folder(self):
        if self.vehicle_folder_id != self.vehicle_tag_ids.mapped('folder_id'):
            self.vehicle_tag_ids = False
