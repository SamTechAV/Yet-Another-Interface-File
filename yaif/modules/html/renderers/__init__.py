from .form      import render as render_form
from .table     import render as render_table
from .dashboard import render as render_dashboard
from .chat      import render as render_chat

RENDERERS = {
    'form':      render_form,
    'table':     render_table,
    'dashboard': render_dashboard,
    'chat':      render_chat,
}