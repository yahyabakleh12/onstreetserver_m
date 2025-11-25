from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    flash,
    abort,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.utils import secure_filename


def _build_database_uri(app_root: str) -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        if not env_url.startswith("mysql"):
            raise RuntimeError("DATABASE_URL must point to a MySQL database")
        return env_url

    mysql_host = os.environ.get("MYSQL_HOST")
    mysql_db = os.environ.get("MYSQL_DATABASE")
    mysql_user = os.environ.get("MYSQL_USER")
    mysql_password = os.environ.get("MYSQL_PASSWORD")
    mysql_port = os.environ.get("MYSQL_PORT", "3306")

    if mysql_host and mysql_db and mysql_user:
        password = f":{mysql_password}" if mysql_password else ""
        return (
            f"mysql+pymysql://{mysql_user}{password}@{mysql_host}:{mysql_port}/{mysql_db}"
        )

    raise RuntimeError(
        "MySQL configuration missing. Set DATABASE_URL or MYSQL_HOST, MYSQL_DATABASE, "
        "and MYSQL_USER to connect to MySQL."
    )


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-key"),
        SQLALCHEMY_DATABASE_URI=_build_database_uri(app.root_path),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    db = SQLAlchemy(app)

    class TicketBase:
        __abstract__ = True

        id = db.Column(db.Integer, primary_key=True)
        camera_id = db.Column(db.Integer)
        zone_name = db.Column(db.String(50))
        camera_ip = db.Column(db.String(45))
        zone_region = db.Column(db.String(50))
        spot_number = db.Column(db.Integer)
        plate_number = db.Column(db.String(20))
        plate_code = db.Column(db.String(10))
        plate_city = db.Column(db.String(50))
        confidence = db.Column(db.Integer)
        entry_time = db.Column(db.DateTime)
        exit_time = db.Column(db.DateTime)
        status = db.Column(db.String(20))
        parkonic_trip_id = db.Column(db.Integer)
        image_base64 = db.Column(db.Text)
        crop_image_path = db.Column(db.String(255))
        entry_image_path = db.Column(db.String(255))
        exit_image_path = db.Column(db.String(255))
        exit_clip_path = db.Column(db.String(255))
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        process_time_in = db.Column(db.DateTime)
        process_time_out = db.Column(db.DateTime)

        def as_dict(self) -> dict:
            return {
                "id": self.id,
                "camera_id": self.camera_id,
                "zone_name": self.zone_name,
                "camera_ip": self.camera_ip,
                "zone_region": self.zone_region,
                "spot_number": self.spot_number,
                "plate_number": self.plate_number,
                "plate_code": self.plate_code,
                "plate_city": self.plate_city,
                "confidence": self.confidence,
                "entry_time": self.entry_time.isoformat() if self.entry_time else None,
                "exit_time": self.exit_time.isoformat() if self.exit_time else None,
                "status": self.status,
                "parkonic_trip_id": self.parkonic_trip_id,
                "image_base64": self.image_base64,
                "crop_image_path": self.crop_image_path,
                "entry_image_path": self.entry_image_path,
                "exit_image_path": self.exit_image_path,
                "exit_clip_path": self.exit_clip_path,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "process_time_in": self.process_time_in.isoformat()
                if self.process_time_in
                else None,
                "process_time_out": self.process_time_out.isoformat()
                if self.process_time_out
                else None,
            }

    class OcrTicket(TicketBase, db.Model):
        __tablename__ = "ocr_ticket"

    class OmcTicket(TicketBase, db.Model):
        __tablename__ = "omc_ticket"

    def _get_ticket_model(ticket_type: str):
        mapping = {
            "ocr": OcrTicket,
            "omc": OmcTicket,
        }
        model = mapping.get(ticket_type.lower()) if ticket_type else None
        if model is None:
            abort(404)
        return model

    def _ticket_label(ticket_type: str) -> str:
        return "OCR" if ticket_type.lower() == "ocr" else "OMC"

    def create_tables() -> None:
        db.create_all()
        if not OcrTicket.query.first():
            sample_ocr_ticket = OcrTicket(
                camera_id=101,
                zone_name="A1",
                camera_ip="192.168.0.10",
                zone_region="North",
                spot_number=12,
                plate_number="ABC123",
                plate_code="DXB",
                plate_city="Dubai",
                confidence=92,
                entry_time=datetime.utcnow(),
                status="open",
                crop_image_path="/tmp/crop.jpg",
            )
            db.session.add(sample_ocr_ticket)

        if not OmcTicket.query.first():
            sample_omc_ticket = OmcTicket(
                camera_id=201,
                zone_name="B2",
                camera_ip="192.168.0.11",
                zone_region="South",
                spot_number=5,
                plate_number="XYZ789",
                plate_code="AUH",
                plate_city="Abu Dhabi",
                confidence=87,
                entry_time=datetime.utcnow(),
                status="pending",
                entry_image_path="/tmp/entry.jpg",
                crop_image_path="/tmp/crop.jpg",
            )
            db.session.add(sample_omc_ticket)

        db.session.commit()

    with app.app_context():
        create_tables()

    @app.context_processor
    def register_template_utils():
        def image_url(path: Optional[str]):
            if not path:
                return None
            if path.startswith("http://") or path.startswith("https://"):
                return path
            return url_for("static", filename=path.lstrip("/"))

        return {"image_url": image_url}

    @app.route("/")
    def home() -> str:
        return redirect(url_for("list_tickets", ticket_type="ocr"))

    def _extract_ticket_data(payload: dict) -> dict:
        return {
            "camera_id": _to_int(payload.get("camera_id")),
            "zone_name": payload.get("zone_name"),
            "camera_ip": payload.get("camera_ip"),
            "zone_region": payload.get("zone_region"),
            "spot_number": _to_int(payload.get("spot_number")),
            "plate_number": payload.get("plate_number"),
            "plate_code": payload.get("plate_code"),
            "plate_city": payload.get("plate_city"),
            "confidence": _to_int(payload.get("confidence")),
            "entry_time": _parse_datetime(payload.get("entry_time")),
            "exit_time": _parse_datetime(payload.get("exit_time")),
            "status": payload.get("status"),
            "parkonic_trip_id": _to_int(payload.get("parkonic_trip_id")),
            "process_time_in": _parse_datetime(payload.get("process_time_in")),
            "process_time_out": _parse_datetime(payload.get("process_time_out")),
            "image_base64": payload.get("image_base64"),
            "crop_image_path": payload.get("crop_image_path"),
            "entry_image_path": payload.get("entry_image_path"),
            "exit_image_path": payload.get("exit_image_path"),
            "exit_clip_path": payload.get("exit_clip_path"),
        }

    def _save_uploaded_image(upload, ticket_type: str, category: str) -> Optional[str]:
        if not upload or not upload.filename:
            return None

        upload_dir = os.path.join(
            app.root_path, "static", "uploads", ticket_type.lower(), category
        )
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(upload.filename) or f"{category}.jpg"
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        final_name = f"{timestamp}_{filename}"
        save_path = os.path.join(upload_dir, final_name)
        upload.save(save_path)

        return os.path.relpath(save_path, os.path.join(app.root_path, "static"))

    def _populate_ticket_from_request(ticket, ticket_type: str):
        form_data = request.form.to_dict() if request.form else {}
        json_data = request.get_json(silent=True) or {}
        data = {**json_data, **form_data}
        provided_keys = set(data.keys())

        entry_path = _save_uploaded_image(
            request.files.get("entry_image"), ticket_type, "entry"
        )
        exit_path = _save_uploaded_image(
            request.files.get("exit_image"), ticket_type, "exit"
        )
        crop_path = _save_uploaded_image(
            request.files.get("crop_image"), ticket_type, "crop"
        )

        payload = _extract_ticket_data(data)

        payload["entry_image_path"] = entry_path or (
            payload.get("entry_image_path")
            if "entry_image_path" in provided_keys
            else getattr(ticket, "entry_image_path", None)
        )
        payload["exit_image_path"] = exit_path or (
            payload.get("exit_image_path")
            if "exit_image_path" in provided_keys
            else getattr(ticket, "exit_image_path", None)
        )
        payload["crop_image_path"] = crop_path or (
            payload.get("crop_image_path")
            if "crop_image_path" in provided_keys
            else getattr(ticket, "crop_image_path", None)
        )

        for key, value in payload.items():
            if value is None and key not in provided_keys:
                value = getattr(ticket, key)
            setattr(ticket, key, value)

        return ticket

    @app.route("/<string:ticket_type>/tickets", methods=["GET"])
    def list_tickets(ticket_type: str) -> str:
        model = _get_ticket_model(ticket_type)
        tickets = model.query.order_by(model.created_at.desc()).all()
        return render_template(
            "tickets.html",
            tickets=tickets,
            ticket_type=ticket_type,
            ticket_label=_ticket_label(ticket_type),
        )

    @app.route("/api/<string:ticket_type>/tickets", methods=["GET", "POST"])
    def api_list_tickets(ticket_type: str):
        model = _get_ticket_model(ticket_type)

        if request.method == "GET":
            tickets = model.query.order_by(model.created_at.desc()).all()
            return jsonify([ticket.as_dict() for ticket in tickets])

        ticket = model()
        _populate_ticket_from_request(ticket, ticket_type)
        db.session.add(ticket)
        db.session.commit()
        return jsonify(ticket.as_dict()), 201

    @app.route("/<string:ticket_type>/tickets/new", methods=["GET", "POST"])
    def create_ticket(ticket_type: str) -> str:
        model = _get_ticket_model(ticket_type)
        if request.method == "POST":
            ticket = model()
            _populate_ticket_from_request(ticket, ticket_type)
            db.session.add(ticket)
            db.session.commit()
            flash(f"{_ticket_label(ticket_type)} ticket created", "success")
            return redirect(url_for("list_tickets", ticket_type=ticket_type))

        return render_template(
            "ticket_form.html",
            ticket=None,
            ticket_type=ticket_type,
            ticket_label=_ticket_label(ticket_type),
        )

    @app.route("/<string:ticket_type>/tickets/<int:ticket_id>/edit", methods=["GET", "POST"])
    def edit_ticket(ticket_type: str, ticket_id: int) -> str:
        model = _get_ticket_model(ticket_type)
        ticket = model.query.get_or_404(ticket_id)
        if request.method == "POST":
            _populate_ticket_from_request(ticket, ticket_type)
            db.session.commit()
            flash(f"{_ticket_label(ticket_type)} ticket updated", "success")
            return redirect(url_for("list_tickets", ticket_type=ticket_type))

        return render_template(
            "ticket_form.html",
            ticket=ticket,
            ticket_type=ticket_type,
            ticket_label=_ticket_label(ticket_type),
        )

    @app.route("/<string:ticket_type>/tickets/<int:ticket_id>/delete", methods=["POST"])
    def delete_ticket(ticket_type: str, ticket_id: int):
        model = _get_ticket_model(ticket_type)
        ticket = model.query.get_or_404(ticket_id)
        db.session.delete(ticket)
        db.session.commit()
        flash(f"{_ticket_label(ticket_type)} ticket deleted", "info")
        return redirect(url_for("list_tickets", ticket_type=ticket_type))

    @app.route("/api/<string:ticket_type>/tickets/<int:ticket_id>", methods=["GET", "PUT", "DELETE"])
    def api_ticket(ticket_type: str, ticket_id: int):
        model = _get_ticket_model(ticket_type)
        ticket = model.query.get_or_404(ticket_id)
        if request.method == "GET":
            return jsonify(ticket.as_dict())
        if request.method == "DELETE":
            db.session.delete(ticket)
            db.session.commit()
            return ("", 204)

        _populate_ticket_from_request(ticket, ticket_type)
        db.session.commit()
        return jsonify(ticket.as_dict())

    return app


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _to_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value) if value else None
    except ValueError:
        return None


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
