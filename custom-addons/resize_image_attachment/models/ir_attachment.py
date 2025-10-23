from odoo import _, api, fields, models, tools


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self,values):
        if 'datas' in values:
            resize_image = tools.image_resize_image(values['datas'], size=(250, 250), avoid_if_small=True)
            values['datas'] = resize_image
            return super(IrAttachment, self).create(values)

    @api.multi
    def write(self, values):
        if 'datas' in values:
            resize_image = tools.image_resize_image(values['datas'], size=(250, 250), avoid_if_small=True)
            values['datas'] = resize_image
            return super(IrAttachment, self).write(values)

    # @api.model

    # def create(self, values):

    #     attachments = values.get('attachment_ids', [])

    #     for attachment in attachments:

    #         datas_fname = attachment[2].get('datas_fname', '')

    #         if datas_fname.endswith(('.exe', '.bat')):

    #             raise ValidationError('You cannot upload files with .exe or .bat extensions.')

    #     return super(HelpdeskTicket, self).create(values)