# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields


class IrModelFields(models.Model):

    _inherit = 'ir.model.fields'

    # With field type BinaryField or ImageField < BinaryField
    # we have extra information for this field, this is the
    # storage that we will store the image.
    #
    # when user modify it from field that means he wants to store
    # image in different place with other configurations (instead
    # of default config in storage.configuration
    storage_id = fields.Many2one(
        'storage.configuration', string='Custom Storage',
        help=("Select a custom storage configuration. "
              "If the field is empty the default one will be use")
    )
