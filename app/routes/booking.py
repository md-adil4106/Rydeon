"""
Rydeon - Customer Booking & Vehicle Reservation Blueprint
---------------------------------------------------------
Handles vehicle details exploration, reservation scheduling, concurrency-safe
booking creation, document verification uploads, and cancellations.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, jsonify
from app.services import vehicle_service, booking_service, document_service
from app.services.decorators import login_required
from app.services.csrf import validate_csrf_token

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/vehicles/<int:vehicle_id>')
def vehicle_details(vehicle_id):
    """Detailed vehicle overview with full specifications and booking CTA."""
    vehicle = vehicle_service.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        abort(404)

    # Fetch similar vehicles in category
    similar_vehicles = [
        v for v in vehicle_service.get_all_vehicles(category=vehicle['category'])
        if v['id'] != vehicle['id']
    ][:3]

    return render_template(
        'vehicles/details.html',
        vehicle=vehicle,
        similar_vehicles=similar_vehicles
    )

@booking_bp.route('/book/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def book_vehicle(vehicle_id):
    """Reservation form and backend booking processor."""
    vehicle = vehicle_service.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        flash("The selected vehicle could not be found.", "danger")
        return redirect(url_for('frontend.catalogue'))

    user_id = session['user_id']

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            flash("Security check failed (invalid CSRF token). Please resubmit.", "danger")
            return redirect(url_for('booking.book_vehicle', vehicle_id=vehicle_id))

        pickup_date = request.form.get('pickup_date')
        return_date = request.form.get('return_date')
        payment_method = request.form.get('payment_method', 'Credit Card (Visa)')
        doc_file = request.files.get('document_file')

        try:
            booking = booking_service.create_customer_booking(
                user_id=user_id,
                vehicle_id=vehicle_id,
                start_date_val=pickup_date,
                end_date_val=return_date,
                payment_method=payment_method,
                document_file=doc_file
            )
            flash(f"Reservation confirmed! Your booking reference is {booking['booking_reference']}.", "success")
            return redirect(url_for('booking.confirmation', booking_id=booking['booking_id']))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template(
                'bookings/book.html',
                vehicle=vehicle,
                pickup_date=pickup_date,
                return_date=return_date,
                payment_method=payment_method
            ), 400

    # GET Request: pre-fill dates if query parameters passed
    pickup_date = request.args.get('pickup_date', '')
    return_date = request.args.get('return_date', '')

    return render_template(
        'bookings/book.html',
        vehicle=vehicle,
        pickup_date=pickup_date,
        return_date=return_date
    )

@booking_bp.route('/bookings/<int:booking_id>/confirmation')
@login_required
def confirmation(booking_id):
    """Booking confirmation summary with printable voucher."""
    user_id = session['user_id']
    is_admin = session.get('role') == 'admin'

    booking = booking_service.get_booking_by_id(
        booking_id,
        user_id=None if is_admin else user_id
    )

    if not booking:
        abort(404)

    documents = document_service.get_booking_documents(booking_id)

    return render_template(
        'bookings/confirmation.html',
        booking=booking,
        documents=documents
    )

@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    """Customer rental overview displaying upcoming and past bookings."""
    user_id = session['user_id']
    upcoming = booking_service.get_user_upcoming_bookings(user_id)
    past = booking_service.get_user_past_bookings(user_id)

    return render_template(
        'bookings/my_bookings.html',
        upcoming_bookings=upcoming,
        past_bookings=past
    )

@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Allows customer to cancel reservation in accordance with project rules."""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash("Security token validation failed.", "danger")
        return redirect(url_for('booking.my_bookings'))

    user_id = session['user_id']
    try:
        booking_service.cancel_customer_booking(booking_id, user_id)
        flash(f"Booking RYD-BK-{booking_id} has been cancelled successfully. Refund initiated to original payment method.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")

    return redirect(url_for('booking.my_bookings'))

@booking_bp.route('/bookings/<int:booking_id>/upload-document', methods=['POST'])
@login_required
def upload_document(booking_id):
    """Allows uploading driver verification documents for a booking."""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash("Security token validation failed.", "danger")
        return redirect(url_for('booking.confirmation', booking_id=booking_id))

    user_id = session['user_id']
    doc_type = request.form.get('document_type', 'drivers_license')
    file_obj = request.files.get('document_file')

    success, result = document_service.validate_and_save_document(user_id, booking_id, doc_type, file_obj)
    if success:
        flash("Identification document uploaded successfully. Verification status is Pending.", "success")
    else:
        flash(result, "danger")

    return redirect(url_for('booking.confirmation', booking_id=booking_id))
