# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    documents_document_settings = fields.Boolean(related='company_id.documents_document_settings', readonly=False, string="Document")
    document_folder_id = fields.Many2one('documents.folder', related='company_id.document_folder_id', readonly=False, string="Document default workspace")
    document_tag_ids = fields.Many2many('documents.tag', 'document_tags_rel', related='company_id.document_tag_ids', readonly=False, string="Document Tags")

    @api.onchange('document_folder_id')
    def onchange_document_folder(self):
        if self.document_folder_id != self.document_tag_ids.mapped('folder_id'):
            self.document_tag_ids = False
