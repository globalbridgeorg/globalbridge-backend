"""Agregação dos dados do painel da conta business (AgenciaViewSet.painel)."""

from django.db.models import Avg
from django.utils import timezone

from core.models import Agencia, Avaliacao, Favorito, SolicitacaoPaisAdicional


def montar_painel(agencia):
    """Dados agregados do dashboard da conta business — tudo real,
    nada fabricado: vem de Avaliacao, Favorito, Plano, Tag e da
    SolicitacaoAgencia original."""
    avaliacoes_qs = Avaliacao.objects.filter(id_agencia=agencia).select_related('id_usuario').order_by('-id')
    total_avaliacoes = avaliacoes_qs.count()
    nota_media = avaliacoes_qs.aggregate(media=Avg('nota'))['media']
    distribuicao = []
    for estrelas in (5, 4, 3, 2, 1):
        qtd = avaliacoes_qs.filter(nota=estrelas).count()
        distribuicao.append({
            'estrelas': estrelas,
            'quantidade': qtd,
            'largura': round(qtd / total_avaliacoes * 100) if total_avaliacoes else 0,
        })

    favoritos_qs = Favorito.objects.filter(tipo='agencia', objeto_id=agencia.id).select_related('id_usuario')
    ha_30_dias = timezone.now() - timezone.timedelta(days=30)

    planos_qs = agencia.plano_set.select_related('id_programa').all()

    solicitacao = getattr(agencia, 'solicitacao_origem', None)

    paises_pendentes = SolicitacaoPaisAdicional.objects.filter(agencia=agencia, status='pendente').select_related('pais')

    # Ranking: posição da agência entre as demais com sede no mesmo
    # país, por nota média — só faz sentido comparar dentro do mesmo
    # mercado.
    ranking = None
    if agencia.id_estado_id:
        pais_sede = agencia.id_estado.id_pais
        concorrentes = (
            Agencia.objects.filter(id_estado__id_pais=pais_sede, ativo=True)
            .annotate(nota=Avg('avaliacao__nota'))
            .order_by('-nota')
        )
        ids_ordenados = list(concorrentes.values_list('id', flat=True))
        if agencia.id in ids_ordenados:
            ranking = {'posicao': ids_ordenados.index(agencia.id) + 1, 'total': len(ids_ordenados), 'pais': pais_sede.nome}

    campos_completude = [
        ('Descrição preenchida', bool(agencia.descricao.strip())),
        ('"Como funciona" preenchido', bool(agencia.como_funciona.strip())),
        ('Imagem de capa enviada', bool(agencia.imagem_capa)),
        ('Layout personalizado', bool(agencia.layout)),
        ('Ao menos 1 programa cadastrado', planos_qs.exists()),
        ('Ao menos 1 especialidade marcada', agencia.tags.exists()),
    ]
    feitos = sum(1 for _, feito in campos_completude if feito)

    paises_atendidos_ids = set(agencia.paises_atendidos.values_list('id', flat=True))

    return {
        'stats': {
            'nota': round(nota_media, 1) if nota_media is not None else None,
            'total_avaliacoes': total_avaliacoes,
            'favoritos': favoritos_qs.count(),
            'favoritos_30_dias': favoritos_qs.filter(criado_em__gte=ha_30_dias).count(),
            'programas': planos_qs.count(),
            'paises': len(paises_atendidos_ids),
        },
        'ranking': ranking,
        'distribuicao_notas': distribuicao,
        'completude': {
            'percentual': round(feitos / len(campos_completude) * 100) if campos_completude else 0,
            'itens': [{'texto': texto, 'feito': feito} for texto, feito in campos_completude],
        },
        'paises_atendidos': [{'id': p.id, 'nome': p.nome, 'sigla': p.codigo_iso} for p in agencia.paises_atendidos.all()],
        'paises_pendentes': [{'id': s.pais.id, 'nome': s.pais.nome, 'sigla': s.pais.codigo_iso} for s in paises_pendentes],
        'planos': [
            {
                'id': p.id, 'nome': p.id_programa.nome,
                'duracao': f'{p.id_programa.duracao_min} a {p.id_programa.duracao_max} semanas',
                'preco': float(p.preco),
            }
            for p in planos_qs
        ],
        'tags': [t.label or t.valor for t in agencia.tags.all()],
        'contato': {
            'email': agencia.contato, 'telefone': agencia.telefone,
            'site': agencia.site, 'endereco': agencia.endereco,
        },
        'verificacao': {
            'responsavel': solicitacao.nome_responsavel if solicitacao else None,
            'cargo': solicitacao.cargo_responsavel if solicitacao else None,
            'enviado_em': solicitacao.criado_em if solicitacao else None,
            'aprovado_em': solicitacao.revisado_em if solicitacao else None,
        } if solicitacao else None,
        'avaliacoes_recentes': [
            {
                'nome': a.id_usuario.name or a.id_usuario.email,
                'nota': a.nota,
                'comentario': a.comentario,
            }
            for a in avaliacoes_qs[:5]
        ],
        'favoritos_recentes': [
            {
                'nome': f.id_usuario.name or f.id_usuario.email,
                'quando': f.criado_em,
            }
            for f in favoritos_qs.order_by('-criado_em')[:6]
        ],
    }
