import os
from uuid import uuid4
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from . import login_required, role_required
from .models import Adjunto, Consulta, ESTADOS_CONSULTA, HistorialActividad, User, db

bp = Blueprint('main', __name__)


def registrar_evento(consulta_id: int, usuario_id: int, tipo: str, descripcion: str) -> None:
    db.session.add(
        HistorialActividad(
            consulta_id=consulta_id,
            usuario_id=usuario_id,
            tipo_evento=tipo,
            descripcion=descripcion,
        )
    )


def allowed_file(filename: str) -> bool:
    return '.' in filename


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email, activo=True).first()
        if not user or not user.check_password(password):
            flash('Credenciales inválidas.', 'danger')
            return render_template('login.html')

        session.clear()
        session['user_id'] = user.id
        flash(f'Bienvenido/a {user.nombre}.', 'success')
        return redirect(url_for('main.home'))

    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('main.login'))


@bp.route('/')
@login_required
def home():
    return render_template('home.html')


@bp.route('/consultas')
@login_required
def consultas_list():
    estado = request.args.get('estado', '').strip()
    responsable = request.args.get('responsable', '').strip()
    search = request.args.get('q', '').strip()

    query = Consulta.query

    if g.user.role == 'vendedor':
        query = query.filter_by(responsable_id=g.user.id)
    if estado:
        query = query.filter_by(estado_actual=estado)
    if responsable and responsable.isdigit() and g.user.role == 'admin':
        query = query.filter_by(responsable_id=int(responsable))
    if search:
        pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Consulta.nombre_contacto.ilike(pattern),
                Consulta.telefono_o_email.ilike(pattern),
            )
        )

    consultas = query.order_by(Consulta.fecha_creacion.desc()).all()
    vendedores = User.query.filter_by(role='vendedor', activo=True).order_by(User.nombre.asc()).all()

    return render_template(
        'consultas_list.html',
        consultas=consultas,
        estados=ESTADOS_CONSULTA,
        vendedores=vendedores,
        filtros={'estado': estado, 'responsable': responsable, 'q': search},
        title='Todas las consultas' if g.user.role == 'admin' else 'Mis consultas',
    )


@bp.route('/mis-consultas')
@login_required
def mis_consultas():
    return redirect(url_for('main.consultas_list'))


@bp.route('/consultas/nueva', methods=['GET', 'POST'])
@role_required('admin')
def consulta_new():
    vendedores = User.query.filter_by(role='vendedor', activo=True).order_by(User.nombre.asc()).all()

    if request.method == 'POST':
        canal = request.form.get('canal', '').strip()
        nombre_contacto = request.form.get('nombre_contacto', '').strip()
        telefono_o_email = request.form.get('telefono_o_email', '').strip()
        texto_consulta = request.form.get('texto_consulta', '').strip()
        observaciones = request.form.get('observaciones_opcionales', '').strip()
        responsable_id = request.form.get('responsable_id', '').strip()

        if canal not in {'WhatsApp', 'Email'}:
            flash('Seleccioná un canal válido.', 'danger')
            return render_template('consulta_new.html', vendedores=vendedores)
        if not all([nombre_contacto, telefono_o_email, texto_consulta, responsable_id]):
            flash('Completá todos los campos obligatorios.', 'danger')
            return render_template('consulta_new.html', vendedores=vendedores)

        consulta = Consulta(
            canal=canal,
            nombre_contacto=nombre_contacto,
            telefono_o_email=telefono_o_email,
            texto_consulta=texto_consulta,
            observaciones_opcionales=observaciones or None,
            responsable_id=int(responsable_id),
        )

        db.session.add(consulta)
        db.session.flush()

        registrar_evento(consulta.id, g.user.id, 'consulta_creada', 'Consulta creada manualmente.')
        registrar_evento(
            consulta.id,
            g.user.id,
            'consulta_asignada',
            f'Asignada al vendedor ID {responsable_id}.',
        )

        files = request.files.getlist('adjuntos')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                original_name = secure_filename(file.filename)
                unique_name = f"{uuid4().hex}_{original_name}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
                file.save(file_path)

                db.session.add(
                    Adjunto(
                        consulta_id=consulta.id,
                        nombre_archivo=original_name,
                        ruta_archivo=unique_name,
                        tipo_mime=file.mimetype or 'application/octet-stream',
                        usuario_que_subio=g.user.id,
                    )
                )
                registrar_evento(
                    consulta.id,
                    g.user.id,
                    'archivo_adjuntado',
                    f'Se adjuntó archivo: {original_name}.',
                )

        db.session.commit()
        flash('Consulta creada correctamente.', 'success')
        return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))

    return render_template('consulta_new.html', vendedores=vendedores)


@bp.route('/consultas/<int:consulta_id>')
@login_required
def consulta_detail(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    if g.user.role == 'vendedor' and consulta.responsable_id != g.user.id:
        flash('No podés ver una consulta no asignada a vos.', 'danger')
        return redirect(url_for('main.consultas_list'))

    vendedores = User.query.filter_by(role='vendedor', activo=True).order_by(User.nombre.asc()).all()
    historial = HistorialActividad.query.filter_by(consulta_id=consulta.id).order_by(HistorialActividad.fecha.desc()).all()

    return render_template('consulta_detail.html', consulta=consulta, estados=ESTADOS_CONSULTA, vendedores=vendedores, historial=historial)


@bp.route('/consultas/<int:consulta_id>/estado', methods=['POST'])
@login_required
def consulta_change_state(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    if g.user.role == 'vendedor' and consulta.responsable_id != g.user.id:
        flash('No podés modificar esta consulta.', 'danger')
        return redirect(url_for('main.consultas_list'))

    nuevo_estado = request.form.get('estado_actual', '').strip()
    if nuevo_estado not in ESTADOS_CONSULTA:
        flash('Estado inválido.', 'danger')
        return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))

    estado_anterior = consulta.estado_actual
    consulta.estado_actual = nuevo_estado
    registrar_evento(
        consulta.id,
        g.user.id,
        'estado_cambiado',
        f'Estado cambiado de {estado_anterior} a {nuevo_estado}.',
    )
    db.session.commit()
    flash('Estado actualizado.', 'success')
    return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))


@bp.route('/consultas/<int:consulta_id>/reasignar', methods=['POST'])
@role_required('admin')
def consulta_reassign(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    nuevo_responsable_id = request.form.get('responsable_id', '').strip()
    if not nuevo_responsable_id.isdigit():
        flash('Responsable inválido.', 'danger')
        return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))

    consulta.responsable_id = int(nuevo_responsable_id)
    registrar_evento(
        consulta.id,
        g.user.id,
        'consulta_asignada',
        f'Reasignada al vendedor ID {nuevo_responsable_id}.',
    )
    db.session.commit()
    flash('Consulta reasignada.', 'success')
    return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))


@bp.route('/consultas/<int:consulta_id>/adjuntar', methods=['POST'])
@login_required
def consulta_upload_file(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    if g.user.role == 'vendedor' and consulta.responsable_id != g.user.id:
        flash('No podés adjuntar en esta consulta.', 'danger')
        return redirect(url_for('main.consultas_list'))

    file = request.files.get('archivo')
    if not file or not file.filename:
        flash('Elegí un archivo para subir.', 'danger')
        return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))

    original_name = secure_filename(file.filename)
    unique_name = f"{uuid4().hex}_{original_name}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
    file.save(file_path)

    db.session.add(
        Adjunto(
            consulta_id=consulta.id,
            nombre_archivo=original_name,
            ruta_archivo=unique_name,
            tipo_mime=file.mimetype or 'application/octet-stream',
            usuario_que_subio=g.user.id,
        )
    )
    registrar_evento(
        consulta.id,
        g.user.id,
        'archivo_adjuntado',
        f'Se adjuntó archivo: {original_name}.',
    )
    db.session.commit()
    flash('Archivo adjuntado.', 'success')
    return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))


@bp.route('/consultas/<int:consulta_id>/nota', methods=['POST'])
@login_required
def consulta_add_note(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    if g.user.role == 'vendedor' and consulta.responsable_id != g.user.id:
        flash('No podés escribir notas en esta consulta.', 'danger')
        return redirect(url_for('main.consultas_list'))

    nota = request.form.get('nota', '').strip()
    if not nota:
        flash('La nota no puede estar vacía.', 'danger')
        return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))

    anterior = consulta.observaciones_opcionales or ''
    consulta.observaciones_opcionales = f"{anterior}\n- {nota}".strip()
    registrar_evento(consulta.id, g.user.id, 'nota_agregada', f'Nota agregada: {nota}')
    db.session.commit()
    flash('Nota guardada.', 'success')
    return redirect(url_for('main.consulta_detail', consulta_id=consulta.id))


@bp.route('/uploads/<path:filename>')
@login_required
def download_upload(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
