from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort

from extensions import db
from models.student import StudentProfile
from models.offer import Offer, OFFER_STATUSES
from models.activity import ApplicationActivity
from routes.decorators import student_required

offers_bp = Blueprint("offers", __name__, url_prefix="/offers")


def current_profile():
    return StudentProfile.query.filter_by(user_id=session["user_id"]).first_or_404()


def owns_offer(offer):
    prof = current_profile()
    return offer.student_id == prof.id


@offers_bp.route("/")
@student_required
def list_offers():
    prof = current_profile()
    offers = prof.offers.order_by(Offer.created_at.desc()).all()
    return render_template("student/offers.html", offers=offers)


@offers_bp.route("/<int:offer_id>")
@student_required
def detail(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    if not owns_offer(offer):
        abort(403)
    return render_template("student/offer_detail.html", offer=offer)


@offers_bp.route("/<int:offer_id>/decide", methods=["POST"])
@student_required
def decide(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    if not owns_offer(offer):
        abort(403)

    decision = request.form.get("decision")
    if decision not in ("Accepted", "Declined"):
        flash("Invalid decision.", "danger")
        return redirect(url_for("offers.detail", offer_id=offer_id))

    offer.status = decision
    application = offer.application
    application.status = "Accepted" if decision == "Accepted" else "Rejected"
    db.session.add(ApplicationActivity(
        application_id=application.id,
        description=f"Offer {decision.lower()} by student"
    ))
    db.session.commit()
    flash(f"Offer {decision.lower()}.", "success")
    return redirect(url_for("offers.detail", offer_id=offer_id))
