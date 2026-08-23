"""
Database models.
"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager for users."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('Users must have an email address.')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create, save and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User model in the system."""

    TIPO_CHOICES = [
        ('estudante', 'Estudante'),
        ('agencia', 'Agência'),
    ]

    email = models.EmailField(max_length=255, unique=True, verbose_name=_('email'), help_text=_('Email'))
    username = models.SlugField(
        max_length=40, unique=True, blank=True,
        verbose_name=_('nome de usuário'), help_text=_('Usado na URL do perfil público (/usuarios/<username>).'),
    )
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default='estudante',
        verbose_name=_('tipo de conta'), help_text=_('Estudante ou agência de intercâmbio.'),
    )
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('name'), help_text=_('Username'))
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name=_('foto de perfil'),
        help_text=_('Foto de perfil do usuário.'),
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_('Usuário está ativo'), help_text=_('Indica que este usuário está ativo.')
    )
    foto = models.ImageField(upload_to='perfil/', blank=True, null=True) 
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('Usuário é da equipe'),
        help_text=_('Indica que este usuário pode acessar o Admin.'),
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        """Meta options for the model."""

        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self._gerar_username_unico()
        super().save(*args, **kwargs)

    def _gerar_username_unico(self):
        base = slugify(self.name or self.email.split('@')[0]) or 'usuario'
        base = base[:32]
        candidato = base
        sufixo = 1
        while User.objects.filter(username=candidato).exclude(pk=self.pk).exists():
            sufixo += 1
            candidato = f'{base}{sufixo}'
        return candidato
