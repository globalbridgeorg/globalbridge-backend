from django.conf import settings
from django.conf.urls.static import static
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
    AdminAprovarPaisAdicionalView,
    AdminAprovarSolicitacaoAgenciaView,
    AdminDadosView,
    AdminDocumentoUrlView,
    AdminMensagemLidaView,
    AdminRecusarPaisAdicionalView,
    AdminRecusarSolicitacaoAgenciaView,
    AgenciaViewSet,
    AvaliacaoViewSet,
    ContatoCreateView,
    EstadoViewSet,
    EstatisticasView,
    FavoritoViewSet,
    PaisViewSet,
    PlanoViewSet,
    ProgramaViewSet,
    RedefinirSenhaView,
    SolicitacaoAgenciaViewSet,
    SolicitarCodigoCadastroView,
    SolicitarCodigoLoginView,
    SolicitarRedefinicaoSenhaView,
    TagViewSet,
    UserRegistrationView,
    UserViewSet,
    VerificarCodigoCadastroView,
    VerificarCodigoLoginView,
)

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
    path('api/estatisticas/', EstatisticasView.as_view(), name='estatisticas'),
    path('api/contato/', ContatoCreateView.as_view(), name='contato_create'),
    # Painel administrativo da API (consumido por /admin no frontend)
    path('api/admin-painel/dados/', AdminDadosView.as_view(), name='admin_painel_dados'),
    path('api/admin-painel/documento/', AdminDocumentoUrlView.as_view(), name='admin_painel_documento'),
    path(
        'api/admin-painel/solicitacoes-agencia/<int:pk>/aprovar/',
        AdminAprovarSolicitacaoAgenciaView.as_view(),
        name='admin_aprovar_solicitacao_agencia',
    ),
    path(
        'api/admin-painel/solicitacoes-agencia/<int:pk>/recusar/',
        AdminRecusarSolicitacaoAgenciaView.as_view(),
        name='admin_recusar_solicitacao_agencia',
    ),
    path(
        'api/admin-painel/solicitacoes-pais/<int:pk>/aprovar/',
        AdminAprovarPaisAdicionalView.as_view(),
        name='admin_aprovar_pais_adicional',
    ),
    path(
        'api/admin-painel/solicitacoes-pais/<int:pk>/recusar/',
        AdminRecusarPaisAdicionalView.as_view(),
        name='admin_recusar_pais_adicional',
    ),
    path(
        'api/admin-painel/mensagens/<int:pk>/',
        AdminMensagemLidaView.as_view(),
        name='admin_mensagem_lida',
    ),
    # Redefinição de senha e login por código
    path('api/auth/esqueci-senha/', SolicitarRedefinicaoSenhaView.as_view(), name='esqueci_senha'),
    path('api/auth/redefinir-senha/', RedefinirSenhaView.as_view(), name='redefinir_senha'),
    path('api/auth/codigo/solicitar/', SolicitarCodigoLoginView.as_view(), name='codigo_login_solicitar'),
    path('api/auth/codigo/verificar/', VerificarCodigoLoginView.as_view(), name='codigo_login_verificar'),
    # Confirmação de e-mail no cadastro (antes de existir usuário)
    path('api/auth/cadastro/codigo/solicitar/', SolicitarCodigoCadastroView.as_view(), name='codigo_cadastro_solicitar'),
    path('api/auth/cadastro/codigo/verificar/', VerificarCodigoCadastroView.as_view(), name='codigo_cadastro_verificar'),
    # API
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_ENDPOINT, document_root=settings.MEDIA_ROOT)
