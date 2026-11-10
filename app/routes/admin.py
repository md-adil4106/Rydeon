"""
Rydeon - Administrative Operations Blueprint
--------------------------------------------
Provides comprehensive fleet CRUD, booking audits, document verification,
and vehicle return processing strictly for administrators.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.services.decorators import admin_required
from app.services.csrf import validate_csrf_token
from app.services import admin_service, vehicle_service, booking_service

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==============================================================================
# 1. ADMIN DASHBOARD OVERVIEW
# ==============================================================================
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Main administrative dashboard displaying verified MySQL metrics."""
    metrics = admin_service.get_admin_dashboard_metrics()
    recent_bookings = admin_service.get_all_bookings_admin()[:8]
    fleet = vehicle_service.get_all_vehicles()[:8]
    pending_docs = admin_service.get_all_documents_admin(status='pending')[:5]

    return render_template(
        'admin/dashboard.html',
        metrics=metrics,
        recent_bookings=recent_bookings,
        fleet=fleet,
        pending_docs=pending_docs
    )

# ==============================================================================
# 2. VEHICLE FLEET MANAGEMENT (CRUD)
# ==============================================================================
@admin_bp.route('/vehicles')
@admin_required
def vehicles_list():
    """Full fleet inventory management view."""
    category = request.args.get('category')
    search = request.args.get('search')
    fleet = vehicle_service.get_all_vehicles(category=category, search=search)
    return render_template('admin/vehicles/list.html', fleet=fleet, search=search, category=category)

@admin_bp.route('/vehicles/add', methods=['GET', 'POST'])
@admin_required
def vehicle_add():
    """Create a new vehicle in the fleet with photo upload support."""
    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            flash("Security check failed (invalid CSRF token).", "danger")
            return redirect(url_for('admin.vehicle_add'))

        name = request.form.get('name')
        brand = request.form.get('brand')
        category = request.form.get('category')
        registration_number = request.form.get('registration_number')
        seating_capacity = request.form.get('seating_capacity')
        fuel_type = request.form.get('fuel_type')
        transmission = request.form.get('transmission')
        price_per_day = request.form.get('price_per_day')
        description = request.form.get('description')
        status = request.form.get('status', 'available')
        image_file = request.files.get('image_file')
        image_url = request.form.get('image_url')

        try:
            admin_service.add_vehicle(
                name=name, brand=brand, category=category,
                registration_number=registration_number,
                seating_capacity=seating_capacity, fuel_type=fuel_type,
                transmission=transmission, price_per_day=price_per_day,
                description=description, status=status,
                image_file=image_file, image_url=image_url
            )
            flash(f"Vehicle '{name}' successfully added to the fleet.", "success")
            return redirect(url_for('admin.vehicles_list'))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template('admin/vehicles/add.html', form=request.form), 400

    return render_template('admin/vehicles/add.html')

@admin_bp.route('/vehicles/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@admin_required
def vehicle_edit(vehicle_id):
    """Edit vehicle specifications, pricing, image, and availability."""
    vehicle = vehicle_service.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        abort(404)

    if request.method == 'POST':
        csrf_token = request.form.get('csrf_token')
        if not validate_csrf_token(csrf_token):
            flash("Security validation failed.", "danger")
            return redirect(url_for('admin.vehicle_edit', vehicle_id=vehicle_id))

        name = request.form.get('name')
        brand = request.form.get('brand')
        category = request.form.get('category')
        registration_number = request.form.get('registration_number')
        seating_capacity = request.form.get('seating_capacity')
        fuel_type = request.form.get('fuel_type')
        transmission = request.form.get('transmission')
        price_per_day = request.form.get('price_per_day')
        description = request.form.get('description')
        status = request.form.get('status')
        image_file = request.files.get('image_file')
        image_url = request.form.get('image_url')

        try:
            admin_service.update_vehicle(
                vehicle_id=vehicle_id, name=name, brand=brand, category=category,
                registration_number=registration_number, seating_capacity=seating_capacity,
                fuel_type=fuel_type, transmission=transmission, price_per_day=price_per_day,
                description=description, status=status,
                image_file=image_file, image_url=image_url
            )
            flash(f"Vehicle #{vehicle_id} updated successfully.", "success")
            return redirect(url_for('admin.vehicles_list'))
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template('admin/vehicles/edit.html', vehicle=vehicle), 400

    return render_template('admin/vehicles/edit.html', vehicle=vehicle)

@admin_bp.route('/vehicles/<int:vehicle_id>/status', methods=['POST'])
@admin_required
def vehicle_change_status(vehicle_id):
    """Quickly toggles vehicle availability status."""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash("CSRF validation failed.", "danger")
        return redirect(url_for('admin.vehicles_list'))

    new_status = request.form.get('status')
    try:
        admin_service.update_vehicle_status(vehicle_id, new_status)
        flash(f"Vehicle #{vehicle_id} status changed to '{new_status}'.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")

    return redirect(url_for('admin.vehicles_list'))

@admin_bp.route('/vehicles/<int:vehicle_id>/delete', methods=['POST'])
@admin_required
def vehicle_delete(vehicle_id):
    """Deletes a vehicle only when no dependent booking records exist."""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash("CSRF validation failed.", "danger")
        return redirect(url_for('admin.vehicles_list'))

    try:
        admin_service.delete_vehicle(vehicle_id)
        flash(f"Vehicle #{vehicle_id} deleted successfully from fleet inventory.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")

    return redirect(url_for('admin.vehicles_list'))

# ==============================================================================
# 3. BOOKING MANAGEMENT & CONFLICT-AWARE APPROVALS
# ==============================================================================
@admin_bp.route('/bookings')
@admin_required
def bookings_list():
    """All reservations auditing view with search and status filtering."""
    search = request.args.get('search')
    status = request.args.get('status')
    bookings = admin_service.get_all_bookings_admin(search=search, status=status)
    return render_template('admin/bookings/list.html', bookings=bookings, search=search, status=status)

@admin_bp.route('/bookings/<int:booking_id>/status', methods=['POST'])
@admin_required
def booking_update_status(booking_id):
    """Approves, rejects, or updates booking status with conflict prevention."""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash("CSRF validation failed.", "danger")
        return redirect(url_for('admin.bookings_list'))

    new_status = request.form.get('status')
    try:
        admin_service.update_booking_status_admin(booking_id, new_status)
        flash(f"Booking #{booking_id} status updated to '{new_status}'.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")

    return redirect(url_for('admin.bookings_list'))

# ==============================================================================
# 4. DOCUMENT VERIFICATION MANAGEMENT
# ==============================================================================
@admin_bp.route('/documents')
@admin_required
def documents_list():
    """Customer verification documents audit and approval view."""
    status = request.args.get('status')
    documents = admin_service.get_all_documents_admin(status=status)
    return render_template('admin/documents/list.html', documents=documents, status=status)

@admin_bp.route('/documents/<int:document_id>/verify', methods=['POST'])
@admin_required
def document_verify(document_id):
    """Approves or rejects a document with verification notes."""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash("CSRF validation failed.", "danger")
        return redirect(url_for('admin.documents_list'))

    new_status = request.form.get('status')
    remarks = request.form.get('remarks', '')

    try:
        admin_service.verify_document_admin(document_id, new_status, remarks=remarks)
        flash(f"Document #{document_id} marked as '{new_status}'.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")

    return redirect(url_for('admin.documents_list'))

# ==============================================================================
# 5. VEHICLE RETURN MANAGEMENT & LATE CHARGES
# ==============================================================================
@admin_bp.route('/returns')
@admin_required
def returns_overview():
    """Vehicle returns processing dashboard for active rentals."""
    active_rentals = admin_service.get_active_bookings_for_return()
    recent_returns = admin_service.get_all_bookings_admin(status='completed')[:10]
    return render_template('admin/returns/overview.html', active_rentals=active_rentals, recent_returns=recent_returns)

@admin_bp.route('/returns/process', methods=['POST'])
@admin_required
def return_process():
    """Processes vehicle return, computes late return fees, and completes booking."""
    csrf_token = request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        flash("CSRF validation failed.", "danger")
        return redirect(url_for('admin.returns_overview'))

    booking_id = request.form.get('booking_id')
    actual_return_date = request.form.get('actual_return_date')
    vehicle_condition = request.form.get('vehicle_condition', 'Good')
    manual_charges = request.form.get('manual_charges', 0.0)
    remarks = request.form.get('remarks', '')

    try:
        summary = admin_service.process_vehicle_return(
            booking_id=int(booking_id),
            actual_return_dt_val=actual_return_date,
            vehicle_condition=vehicle_condition,
            manual_charges=manual_charges,
            remarks=remarks
        )
        flash(
            f"Vehicle return processed for Booking #{booking_id}! "
            f"Additional charges: ${summary['total_additional_charges']:.2f} "
            f"(Late fee: ${summary['late_fee']:.2f}). Vehicle marked available.",
            "success"
        )
    except (ValueError, TypeError) as exc:
        flash(str(exc), "danger")

    return redirect(url_for('admin.returns_overview'))
