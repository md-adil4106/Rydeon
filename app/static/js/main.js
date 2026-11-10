/**
 * RYDEON - VEHICLE RENTAL SYSTEM
 * Client-Side Interactivity, Dynamic Filtering, and UI Modals
 * (Frontend Preview - Pure Vanilla JS with Bootstrap 5 integration)
 */

document.addEventListener('DOMContentLoaded', () => {
    initDatePickers();
    initCatalogueFiltering();
    initVehicleModal();
    initAuthValidation();
});

/**
 * 1. Initialize Default Dates for Booking Search Bars
 */
function initDatePickers() {
    const pickupInputs = document.querySelectorAll('input[type="date"].pickup-date');
    const returnInputs = document.querySelectorAll('input[type="date"].return-date');

    if (pickupInputs.length === 0) return;

    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    const defaultReturn = new Date(today);
    defaultReturn.setDate(today.getDate() + 5);

    const formatDate = (d) => d.toISOString().split('T')[0];

    pickupInputs.forEach(input => {
        input.min = formatDate(today);
        if (!input.value) input.value = formatDate(tomorrow);

        input.addEventListener('change', () => {
            returnInputs.forEach(retInput => {
                retInput.min = input.value;
                if (retInput.value && retInput.value < input.value) {
                    retInput.value = input.value;
                }
            });
        });
    });

    returnInputs.forEach(input => {
        input.min = formatDate(tomorrow);
        if (!input.value) input.value = formatDate(defaultReturn);
    });
}

/**
 * 2. Vehicle Catalogue Live Filtering & Search
 */
function initCatalogueFiltering() {
    const vehicleCards = document.querySelectorAll('.catalogue-vehicle-item');
    if (vehicleCards.length === 0) return;

    const searchInput = document.getElementById('searchVehicles');
    const categoryPills = document.querySelectorAll('.filter-pill[data-category]');
    const priceSlider = document.getElementById('priceRangeSlider');
    const priceDisplay = document.getElementById('priceDisplayValue');
    const seatSelect = document.getElementById('seatsFilter');
    const fuelSelect = document.getElementById('fuelFilter');
    const emptyState = document.getElementById('noResultsState');
    const countDisplay = document.getElementById('visibleVehicleCount');

    let activeCategory = 'all';

    // Category Pill Click
    categoryPills.forEach(pill => {
        pill.addEventListener('click', (e) => {
            e.preventDefault();
            categoryPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            activeCategory = pill.getAttribute('data-category').toLowerCase();
            applyFilters();
        });
    });

    // Search Input
    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }

    // Price Slider
    if (priceSlider && priceDisplay) {
        priceSlider.addEventListener('input', () => {
            priceDisplay.textContent = `$${priceSlider.value}`;
            applyFilters();
        });
    }

    // Dropdown Filters
    if (seatSelect) seatSelect.addEventListener('change', applyFilters);
    if (fuelSelect) fuelSelect.addEventListener('change', applyFilters);

    function applyFilters() {
        const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const maxPrice = priceSlider ? parseFloat(priceSlider.value) : Infinity;
        const selectedSeats = seatSelect ? seatSelect.value : 'all';
        const selectedFuel = fuelSelect ? fuelSelect.value.toLowerCase() : 'all';

        let visibleCount = 0;

        vehicleCards.forEach(card => {
            const name = (card.getAttribute('data-name') || '').toLowerCase();
            const category = (card.getAttribute('data-category') || '').toLowerCase();
            const price = parseFloat(card.getAttribute('data-price') || '0');
            const seats = card.getAttribute('data-seats') || '';
            const fuel = (card.getAttribute('data-fuel') || '').toLowerCase();

            const matchesQuery = !query || name.includes(query) || category.includes(query);
            const matchesCategory = activeCategory === 'all' || category === activeCategory;
            const matchesPrice = price <= maxPrice;
            const matchesSeats = selectedSeats === 'all' || seats === selectedSeats;
            const matchesFuel = selectedFuel === 'all' || fuel.includes(selectedFuel);

            if (matchesQuery && matchesCategory && matchesPrice && matchesSeats && matchesFuel) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        if (emptyState) {
            emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
        }

        if (countDisplay) {
            countDisplay.textContent = visibleCount;
        }
    }

    // Initialize on page load in case pre-selected category in URL query params
    const urlParams = new URLSearchParams(window.location.search);
    const categoryParam = urlParams.get('category');
    if (categoryParam) {
        const targetPill = document.querySelector(`.filter-pill[data-category="${categoryParam}"]`);
        if (targetPill) {
            targetPill.click();
        }
    }
}

/**
 * 3. Vehicle Details Modal Population
 */
function initVehicleModal() {
    const detailModalEl = document.getElementById('vehicleDetailModal');
    if (!detailModalEl) return;

    detailModalEl.addEventListener('show.bs.modal', (event) => {
        const button = event.relatedTarget;
        if (!button) return;

        const name = button.getAttribute('data-name') || 'Vehicle Details';
        const category = button.getAttribute('data-category') || 'Premium';
        const price = button.getAttribute('data-price') || '0';
        const img = button.getAttribute('data-img') || '';
        const seats = button.getAttribute('data-seats') || '5';
        const transmission = button.getAttribute('data-transmission') || 'Automatic';
        const fuel = button.getAttribute('data-fuel') || 'Gasoline';
        const power = button.getAttribute('data-power') || '400 HP';
        const range = button.getAttribute('data-range') || '25 MPG';
        const tagline = button.getAttribute('data-tagline') || 'Experience luxury performance.';
        const featuresRaw = button.getAttribute('data-features') || '';

        // Populate modal fields
        const modalImg = detailModalEl.querySelector('#modalVehicleImg');
        const modalName = detailModalEl.querySelector('#modalVehicleName');
        const modalCategory = detailModalEl.querySelector('#modalVehicleCategory');
        const modalTagline = detailModalEl.querySelector('#modalVehicleTagline');
        const modalPrice = detailModalEl.querySelector('#modalVehiclePrice');
        const modalPower = detailModalEl.querySelector('#modalVehiclePower');
        const modalTrans = detailModalEl.querySelector('#modalVehicleTransmission');
        const modalFuel = detailModalEl.querySelector('#modalVehicleFuel');
        const modalSeats = detailModalEl.querySelector('#modalVehicleSeats');
        const modalRange = detailModalEl.querySelector('#modalVehicleRange');
        const modalFeaturesList = detailModalEl.querySelector('#modalVehicleFeatures');

        if (modalImg) modalImg.src = img;
        if (modalName) modalName.textContent = name;
        if (modalCategory) modalCategory.textContent = category;
        if (modalTagline) modalTagline.textContent = tagline;
        if (modalPrice) modalPrice.textContent = `$${price}`;
        if (modalPower) modalPower.textContent = power;
        if (modalTrans) modalTrans.textContent = transmission;
        if (modalFuel) modalFuel.textContent = fuel;
        if (modalSeats) modalSeats.textContent = `${seats} Seats`;
        if (modalRange) modalRange.textContent = range;

        if (modalFeaturesList && featuresRaw) {
            try {
                const features = JSON.parse(featuresRaw);
                modalFeaturesList.innerHTML = features.map(f => `
                    <div class="col-sm-6 mb-2">
                        <div class="d-flex align-items-center gap-2">
                            <i class="bi bi-check-circle-fill text-primary"></i>
                            <span class="small fw-semibold text-secondary">${f}</span>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                modalFeaturesList.innerHTML = '';
            }
        }
    });
}

/**
 * 4. Client-side Validation for Auth Forms (Login & Register)
 */
function initAuthValidation() {
    const registerForm = document.getElementById('registrationForm');
    const loginForm = document.getElementById('loginForm');

    if (registerForm) {
        const pass = document.getElementById('regPassword');
        const confirmPass = document.getElementById('regConfirmPassword');
        const feedback = document.getElementById('passwordFeedback');

        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (pass && confirmPass && pass.value !== confirmPass.value) {
                if (feedback) feedback.style.display = 'block';
                confirmPass.classList.add('is-invalid');
                return;
            }
            // Frontend demo notification & redirect
            alert('Registration form validated successfully! Redirecting to Customer Dashboard preview.');
            window.location.href = '/dashboard';
        });

        if (confirmPass && pass) {
            confirmPass.addEventListener('input', () => {
                if (confirmPass.value === pass.value) {
                    confirmPass.classList.remove('is-invalid');
                    confirmPass.classList.add('is-valid');
                    if (feedback) feedback.style.display = 'none';
                } else {
                    confirmPass.classList.add('is-invalid');
                    confirmPass.classList.remove('is-valid');
                    if (feedback) feedback.style.display = 'block';
                }
            });
        }
    }

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Frontend demo redirect to dashboard
            window.location.href = '/dashboard';
        });
    }
}
