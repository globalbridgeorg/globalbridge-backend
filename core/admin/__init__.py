"""
Django admin customization — cada submódulo registra os ModelAdmins da sua área.
"""

from . import agencia, catalogo, solicitacoes, usuarios  # noqa: F401
