"""Rotas HTTP do Clube Aurora."""

from flask import Blueprint, g, jsonify, request

from . import auth, db

bp = Blueprint("main", __name__)

VALID_SERVICES = {"viagem", "arte", "evento"}
VALID_ROLES = {"staff", "admin"}


@bp.get("/")
def index():
    return jsonify(message="Clube Aurora API", status="ok")


@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.get("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /admin\n", 200, {"Content-Type": "text/plain"}


@bp.get("/sitemap.xml")
def sitemap():
    return "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"><url><loc>http://localhost:8080/</loc></url></urlset>", 200, {"Content-Type": "application/xml"}


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email, password = data.get("email", ""), data.get("password", "")
    user = auth.authenticate(email, password)
    if user is None:
        return jsonify(error="credenciais inválidas"), 401
    return jsonify(token=auth.issue_token(user["id"]), role=user["role"])


# ---------------------------------------------------------------- clientes

@bp.get("/clients")
@auth.login_required
def clients():
    return jsonify(db.list_clients())


@bp.get("/clients/search")
@auth.login_required
def clients_search():
    name = request.args.get("name", "")
    return jsonify(db.search_clients(name))


@bp.get("/clients/<int:client_id>/bookings")
@auth.login_required
def bookings_list(client_id):
    if db.get_client(client_id) is None:
        return jsonify(error="cliente não encontrado"), 404
    return jsonify(db.list_bookings(client_id))


@bp.post("/clients/<int:client_id>/bookings")
@auth.login_required
def bookings_create(client_id):
    if db.get_client(client_id) is None:
        return jsonify(error="cliente não encontrado"), 404
    data = request.get_json(silent=True) or {}
    service = data.get("service")
    destination = data.get("destination")
    starts_at = data.get("starts_at")
    amount = data.get("amount")
    if service not in VALID_SERVICES or not destination or not starts_at:
        return jsonify(error="dados inválidos"), 400
    if not isinstance(amount, (int, float)) or amount < 0:
        return jsonify(error="valor inválido"), 400
    booking_id = db.create_booking(client_id, g.user["id"], service, destination, starts_at, amount)
    return jsonify(id=booking_id), 201


# ---------------------------------------------------------------- admin

@bp.get("/admin/users")
@auth.require_role("admin")
def admin_users():
    return jsonify(db.list_users())


@bp.post("/admin/users/<int:user_id>/role")
@auth.require_role("admin")
def admin_set_role(user_id):
    role = (request.get_json(silent=True) or {}).get("role")
    if role not in VALID_ROLES:
        return jsonify(error="papel inválido"), 400
    if db.set_user_role(user_id, role) == 0:
        return jsonify(error="usuário não encontrado"), 404
    db.log_action(g.user["id"], f"role_change:{user_id}:{role}")
    return jsonify(id=user_id, role=role)
