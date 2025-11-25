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


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{os.path.join(app.root_path, 'tickets.db')}"
        ),
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

    @app.before_first_request
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
            )
            db.session.add(sample_omc_ticket)

        db.session.commit()

    @app.route("/")
    def home() -> str:
        return redirect(url_for("list_tickets", ticket_type="ocr"))

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

    @app.route("/<string:ticket_type>/tickets/new", methods=["GET", "POST"])
    def create_ticket(ticket_type: str) -> str:
        model = _get_ticket_model(ticket_type)
        if request.method == "POST":
            ticket = model(
                camera_id=_to_int(request.form.get("camera_id")),
                zone_name=request.form.get("zone_name"),
                camera_ip=request.form.get("camera_ip"),
                zone_region=request.form.get("zone_region"),
                spot_number=_to_int(request.form.get("spot_number")),
                plate_number=request.form.get("plate_number"),
                plate_code=request.form.get("plate_code"),
                plate_city=request.form.get("plate_city"),
                confidence=_to_int(request.form.get("confidence")),
                entry_time=_parse_datetime(request.form.get("entry_time")),
                exit_time=_parse_datetime(request.form.get("exit_time")),
                status=request.form.get("status"),
                parkonic_trip_id=_to_int(request.form.get("parkonic_trip_id")),
                process_time_in=_parse_datetime(request.form.get("process_time_in")),
                process_time_out=_parse_datetime(request.form.get("process_time_out")),
                image_base64=request.form.get("image_base64"),
                crop_image_path=request.form.get("crop_image_path"),
                entry_image_path=request.form.get("entry_image_path"),
                exit_image_path=request.form.get("exit_image_path"),
                exit_clip_path=request.form.get("exit_clip_path"),
            )
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
            ticket.camera_id = _to_int(request.form.get("camera_id"))
            ticket.zone_name = request.form.get("zone_name")
            ticket.camera_ip = request.form.get("camera_ip")
            ticket.zone_region = request.form.get("zone_region")
            ticket.spot_number = _to_int(request.form.get("spot_number"))
            ticket.plate_number = request.form.get("plate_number")
            ticket.plate_code = request.form.get("plate_code")
            ticket.plate_city = request.form.get("plate_city")
            ticket.confidence = _to_int(request.form.get("confidence"))
            ticket.entry_time = _parse_datetime(request.form.get("entry_time"))
            ticket.exit_time = _parse_datetime(request.form.get("exit_time"))
            ticket.status = request.form.get("status")
            ticket.parkonic_trip_id = _to_int(request.form.get("parkonic_trip_id"))
            ticket.process_time_in = _parse_datetime(request.form.get("process_time_in"))
            ticket.process_time_out = _parse_datetime(request.form.get("process_time_out"))
            ticket.image_base64 = request.form.get("image_base64")
            ticket.crop_image_path = request.form.get("crop_image_path")
            ticket.entry_image_path = request.form.get("entry_image_path")
            ticket.exit_image_path = request.form.get("exit_image_path")
            ticket.exit_clip_path = request.form.get("exit_clip_path")
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

    @app.route("/api/<string:ticket_type>/tickets", methods=["GET"])
    def api_list_tickets(ticket_type: str):
        model = _get_ticket_model(ticket_type)
        tickets = model.query.order_by(model.created_at.desc()).all()
        return jsonify([ticket.as_dict() for ticket in tickets])

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

        data = request.get_json(force=True)
        ticket.camera_id = _to_int(data.get("camera_id"))
        ticket.zone_name = data.get("zone_name")
        ticket.camera_ip = data.get("camera_ip")
        ticket.zone_region = data.get("zone_region")
        ticket.spot_number = _to_int(data.get("spot_number"))
        ticket.plate_number = data.get("plate_number")
        ticket.plate_code = data.get("plate_code")
        ticket.plate_city = data.get("plate_city")
        ticket.confidence = _to_int(data.get("confidence"))
        ticket.entry_time = _parse_datetime(data.get("entry_time"))
        ticket.exit_time = _parse_datetime(data.get("exit_time"))
        ticket.status = data.get("status")
        ticket.parkonic_trip_id = _to_int(data.get("parkonic_trip_id"))
        ticket.process_time_in = _parse_datetime(data.get("process_time_in"))
        ticket.process_time_out = _parse_datetime(data.get("process_time_out"))
        ticket.image_base64 = data.get("image_base64")
        ticket.crop_image_path = data.get("crop_image_path")
        ticket.entry_image_path = data.get("entry_image_path")
        ticket.exit_image_path = data.get("exit_image_path")
        ticket.exit_clip_path = data.get("exit_clip_path")
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
