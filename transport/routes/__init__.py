# --- register submodules so their routes attach to admin_bp ---
from . import companies       # /admin/company/*
from . import agreements      # /admin/agreement/*
from . import lorries         # /admin/lorry/*
from . import authorities     # /admin/authority/*
from . import routes as routes_mod   # /admin/route/*
from . import letters         # /admin/letter/*
