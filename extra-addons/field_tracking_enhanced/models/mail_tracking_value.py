# -*- coding: utf-8 -*-
"""
@File    : mail_tracking_value.py
@Time    : 2024/10/14
@Author  : XSK
@Version : 16.0
@Contact : chiyuan@workdomain.top
@Desc    : 字段变更记录表
"""
from odoo import fields, models, api


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    @api.model
    def create_tracking_values(self, initial_value, new_value, col_name, col_info, tracking_sequence, model_name):
        res = super().create_tracking_values(initial_value, new_value, col_name, col_info, tracking_sequence, model_name)
        try:
            field = self.env['ir.model.fields']._get(model_name, col_name)
            if field:
                values = {'field': field.id, 'field_desc': col_info['string'], 'field_type': col_info['type'], 'tracking_sequence': tracking_sequence}
                if col_info['type'] == 'many2many':
                    values.update({
                        'field_type': 'text',
                        'old_value_text': initial_value and '、'.join([v[1] for v in initial_value.sudo().name_get()]) or '',
                        'new_value_text': new_value and '、'.join([v[1] for v in new_value.sudo().name_get()]) or ''
                    })
                    return values
        except Exception as e:
            pass
        return res
