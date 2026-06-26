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
    UserRegistrationView, 
    UserViewSet, 
    PaisViewSet,     
    AgenciaViewSet,  
    AvaliacaoViewSet,
    EstadoViewSet,   
    PlanoViewSet,    
    ProgramaViewSet  
)

router = DefaultRouter()

router.register(r'usuarios', UserViewSet, basename='usuarios')
router.register(r'paises', PaisViewSet, basename='paises')
router.register(r'agencia', AgenciaViewSet, basename='agencia')
router.register(r'avaliacao', AvaliacaoViewSet, basename='avaliacao')
router.register(r'estado', EstadoViewSet, basename='estado')
router.register(r'plano', PlanoViewSet, basename='plano')
router.register(r'programa', ProgramaViewSet, basename='programa')

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
    # API
    path('api/', include(router.urls)),
    path('', include(router.urls)),
]
