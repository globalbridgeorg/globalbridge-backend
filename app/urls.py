from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from core.views import (
    UploadFotoPerfilView,
    UserRegistrationView,
    UserViewSet,
    PaisViewSet,
    AgenciaViewSet,
    AvaliacaoViewSet,
    EstadoViewSet,
    PlanoViewSet,
    ProgramaViewSet,
    TagViewSet,
    EstatisticasView,
    FavoritoViewSet,
    SolicitacaoAgenciaViewSet,
    SolicitarRedefinicaoSenhaView,
    RedefinirSenhaView,
    SolicitarCodigoLoginView,
    VerificarCodigoLoginView,
)

from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()

router.register(r'usuarios', UserViewSet, basename='usuarios')
router.register(r'paises', PaisViewSet, basename='paises')
router.register(r'agencia', AgenciaViewSet, basename='agencia')
router.register(r'avaliacao', AvaliacaoViewSet, basename='avaliacao')
router.register(r'estado', EstadoViewSet, basename='estado')
router.register(r'plano', PlanoViewSet, basename='plano')
router.register(r'programa', ProgramaViewSet, basename='programa')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'favoritos', FavoritoViewSet, basename='favoritos')
router.register(r'solicitacoes-agencia', SolicitacaoAgenciaViewSet, basename='solicitacoes-agencia')

urlpatterns = [
    path('admin/', admin.site.urls),
    # OpenAPI 3
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/doc/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    # Autenticação JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Registro de usuários
    path('api/registro/', UserRegistrationView.as_view(), name='user_registration'),
    # Local dev root aliases (frontend may use base URL without /api)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair_root'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh_root'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify_root'),
    path('registro/', UserRegistrationView.as_view(), name='user_registration_root'),
    path('perfil/foto/', UserViewSet.as_view({'patch': 'foto'}), name='perfil_foto'),
    path('api/estatisticas/', EstatisticasView.as_view(), name='estatisticas'),
    # Redefinição de senha e login por código
    path('api/auth/esqueci-senha/', SolicitarRedefinicaoSenhaView.as_view(), name='esqueci_senha'),
    path('api/auth/redefinir-senha/', RedefinirSenhaView.as_view(), name='redefinir_senha'),
    path('api/auth/codigo/solicitar/', SolicitarCodigoLoginView.as_view(), name='codigo_login_solicitar'),
    path('api/auth/codigo/verificar/', VerificarCodigoLoginView.as_view(), name='codigo_login_verificar'),
    # API
    path('api/', include(router.urls)),
    path('', include(router.urls)),
]
