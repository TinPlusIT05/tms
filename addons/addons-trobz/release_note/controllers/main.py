# -*- coding: utf-8 -*-

#####################################################################
#                © 2016 Trobz http://www.trobz.com                  #
#                                                                   #
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).#
#####################################################################

import os

from openerp.modules import module
from openerp import http


class ReleaseNote(http.Controller):

    @http.route('/web/webclient/release_note', type='json', auth="user")
    def release_note(self):
        # get release_note module path
        release_note = module.get_module_path('release_note')

        # get RELEASE-NOTES.md file path
        release_note_file_path = os.path.join(
            release_note, "../../../RELEASE-NOTES.md")

        f = open(release_note_file_path, 'rb')
        return f.read()
