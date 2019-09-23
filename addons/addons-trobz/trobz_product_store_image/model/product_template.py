# -*- coding: utf-8 -*-
from openerp import models, fields


class product_template(models.Model):

    _inherit = 'product.template'

    image_small = fields.ImageField(
        string="Small-sized photo",
        resize_based_on='image_medium', width=64, height=64,
        help="Small-sized photo of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required."
    )

    image_medium = fields.ImageField(
        string="Medium-sized photo", width=128, height=128,
        help="Medium-sized photo of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views."
    )

