from .user import UserRegistrationView, UserViewSet, UploadFotoPerfilView
from .pais import PaisViewSet
from .agencia import AgenciaViewSet   
from .avaliacao import AvaliacaoViewSet
from .estado import EstadoViewSet
from .plano import PlanoViewSet
from .programa import ProgramaViewSet
from .tag import TagViewSet
from .estatisticas import EstatisticasView
from .favorito import FavoritoViewSet
from .solicitacao_agencia import SolicitacaoAgenciaViewSet
from .auth import (
    SolicitarRedefinicaoSenhaView,
    RedefinirSenhaView,
    SolicitarCodigoLoginView,
    VerificarCodigoLoginView,
)
