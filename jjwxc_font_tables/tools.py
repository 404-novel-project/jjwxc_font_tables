import os
import tempfile

from flask import (
    Blueprint, render_template, make_response, abort, request, Flask, current_app, redirect, flash,
    send_from_directory
)
from werkzeug.utils import secure_filename

from .font_parser import validator
from .font_parser.slow import (
    save_std_im_np_arrays, load_SourceHanSansSC_Normal, load_SourceHanSansSC_Regular
)
from .font_parser.tools import match_jjwxc_font_tool, match_upload_font_tool

bp = Blueprint('tools', __name__, url_prefix='/tools')


@bp.route('/')
def get_tools():
    return render_template('tools/index.html')


@bp.route('/slow-match/jjwxc', methods=('GET', 'POST'))
async def slow_match_jjwxc():
    if request.method == 'POST':
        jjwxc_font_name = request.form['jjwxc_font_name']
        if not validator(jjwxc_font_name):
            return abort(403)

        result, status = await match_jjwxc_font_tool(jjwxc_font_name,
                                                     {"std_font": request.form['std_font'],
                                                      "guest_range": request.form['guest_range']})
        if status == 200:
            return make_response(result)
        else:
            return abort(status)

    return render_template('tools/slow_match_jjwxc.html')


@bp.route('/slow-match/upload', methods=('GET', 'POST'))
async def slow_match_upload():
    if request.method == 'POST':
        if 'upload_font' not in request.files:
            flash('未发现文件！')
            return redirect(request.url)

        upload_font = request.files['upload_font']
        upload_font_bytes = upload_font.stream.read()

        with open(os.path.join(
                current_app.config.get('UPLOAD_FOLDER'), secure_filename(upload_font.filename)
        ), 'wb') as f:
            f.write(upload_font_bytes)

        result, status = await match_upload_font_tool(upload_font.filename, upload_font_bytes, upload_font.mimetype,
                                                      {"std_font": request.form['std_font'],
                                                       "guest_range": request.form['guest_range']})
        if status == 200:
            return make_response(result)
        else:
            return abort(status)

    return render_template('tools/slow_match_upload.html')


@bp.route('/slow-match/upload-font/<filename>')
def get_slow_match_upload_font(filename):
    return send_from_directory(
        current_app.config.get('UPLOAD_FOLDER'),
        filename
    )


def init_app(app: Flask):
    tempfolder = tempfile.mkdtemp()
    app.config.from_mapping(
        UPLOAD_FOLDER=tempfolder
    )
    current_app.logger.info('create temp upload folder: {}'.format(tempfolder))

    if not os.path.exists(app.config.get('SOURCE_HAN_SANS_SC_NORMAL_NPZ_PATH')):
        current_app.logger.info('save SourceHanSansSC_Normal npz')
        save_std_im_np_arrays(load_SourceHanSansSC_Normal(), app.config.get('SOURCE_HAN_SANS_SC_NORMAL_NPZ_PATH'))

    if not os.path.exists(app.config.get('SOURCE_HAN_SANS_SC_REGULARL_NPZ_PATH')):
        current_app.logger.info('save SourceHanSansSC_Regular npz')
        save_std_im_np_arrays(load_SourceHanSansSC_Regular(), app.config.get('SOURCE_HAN_SANS_SC_REGULARL_NPZ_PATH'))
