import pytest
from app import create_app
from config.config import Config

class TestConfig(Config):
    TESTING = True
    DEBUG = False

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client

def test_landing_page(client):
    """Test landing page loads successfully with hero and featured fleet."""
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "RYDEON" in html
    assert "Featured Vehicles" in html
    assert "Find Your Vehicle" in html
    assert "Why Discerning Drivers Choose Rydeon" in html

def test_catalogue_page(client):
    """Test vehicle catalogue loads with filters and vehicles."""
    response = client.get('/catalogue')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Premier Vehicle Fleet" in html
    assert "Filter Fleet" in html
    assert "Porsche Taycan 4S" in html
    assert "Mercedes-Benz S-Class" in html

def test_catalogue_alias_route(client):
    """Test /vehicles alias route resolves to catalogue."""
    response = client.get('/vehicles')
    assert response.status_code == 200
    assert "Premier Vehicle Fleet" in response.data.decode('utf-8')

def test_login_page(client):
    """Test login screen loads with email and password inputs."""
    response = client.get('/login')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Sign In to Account" in html
    assert "loginEmail" in html
    assert "loginPassword" in html
    assert "Frontend Preview" in html

def test_register_page(client):
    """Test registration screen loads with full name, email, phone and passwords."""
    response = client.get('/register')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Create Your Account" in html
    assert "regFullName" in html
    assert "regEmail" in html
    assert "regPhone" in html
    assert "regPassword" in html
    assert "regConfirmPassword" in html

def test_dashboard_page(client):
    """Test customer dashboard displays active booking, stats, and history."""
    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Welcome back" in html
    assert "Current & Upcoming Booking" in html
    assert "Booking History" in html
    assert "Active Rentals" in html

def test_static_assets(client):
    """Test that custom CSS and JS are served properly."""
    css_resp = client.get('/static/css/style.css')
    assert css_resp.status_code == 200
    assert "--navy-primary" in css_resp.data.decode('utf-8')

    js_resp = client.get('/static/js/main.js')
    assert js_resp.status_code == 200
    assert "RYDEON" in js_resp.data.decode('utf-8')
