# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for Odoo
#   Copyright (C) 2015 Trobz (http://www.trobz.com).
#   @author Tran Quang Tri <tri@trobz.com>
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

import openerp
from openerp.osv import fields
from openerp.models import FIELDS_TO_PGTYPES


class secure(fields._column):

    _prefetch = False

    _type = 'secure'

# ==========================================
# make a patch to current fields system (V7)
# ==========================================
openerp.osv.fields.secure = secure
FIELDS_TO_PGTYPES[openerp.osv.fields.secure] = 'text'
