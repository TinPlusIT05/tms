# -*- coding: utf-8 -*-
from openerp import models, fields


class product_product(models.Model):

    _inherit = 'product.product'

    image_medium = fields.ImageField(
        string="Medium-sized photo", width=128, height=128,
        help="Medium-sized photo of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views."
    )

    image_small = fields.ImageField(
        string="Small-sized photo",
        resize_based_on='image_medium', width=64, height=64,
        help="Small-sized photo of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required."
    )

    image_variant = fields.ImageField(
        string="Variant Image", width=1024, height=1024,
        help="This field holds the image used as image for the product "
             "variant, limited to 1024x1024px."
    )

