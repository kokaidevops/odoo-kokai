from odoo import _, api, fields, models


class BaseDocument(models.Model):
    _name = 'base.document'
    _inherit = ['base.document', 'documents.mixin']

    def _get_document_tags(self):
        if self.based_on == 'fleet':
            return self.company_id.vehicle_tag_ids
        return super()._get_document_tags()

    def _get_document_folder(self):
        if self.based_on == 'fleet':
            return self.company_id.vehicle_folder_id
        return super()._get_document_folder()

    def _get_document_partner(self):
        return self.partner_id

    def _check_create_documents(self):
        if self.based_on == 'fleet':
            return self.company_id.documents_vehicle_settings and super()._check_create_documents()
        return super()._check_create_documents()

    def action_open_attachments(self):
        if not (self.company_id.documents_vehicle_settings and self.based_on == 'fleet'):
            return super().action_open_attachments()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'documents.document',
            'name': _('Documents'),
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', 'base.document'), ('res_id', 'in', self.ids)],
            # 'context': {
            #     'searchpanel_default_folder_id': self._get_document_folder().id,
            #     'default_res_model': 'base.document',
            #     'default_res_id': self.ids[0],
            # },
        }

    based_on = fields.Selection(selection_add=[('fleet', 'Fleet')], ondelete={'fleet': 'cascade'}, string='Based On')
    fleet_id = fields.Many2one('fleet.vehicle', string='Fleet')