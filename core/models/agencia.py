from django.conf import settings
from django.db import models

class Agencia(models.Model):
    nome = models.CharField(max_length=50)
    descricao = models.TextField()
    como_funciona = models.TextField(
        blank=True, default='',
        verbose_name="Como funciona",
        help_text="Explicação, em texto livre, de como é o processo de inscrição/atendimento dessa agência.",
    )
    contato =   models.CharField(max_length=100)
    telefone =  models.CharField(max_length=20)
    site = models.CharField(max_length=255)
    endereco = models.TextField()
    data_cadastro = models.DateTimeField()
    ativo = models.BooleanField()
    id_estado = models.ForeignKey(
        'Estado', on_delete=models.SET_NULL, null=True, blank=True, related_name='agencias',
        verbose_name="Sede", help_text="Cidade/estado da sede da agência — usado no endereço e como localização principal.",
    )
    # Nem toda agência atua num país só (ex.: EF Education tem unidades em
    # vários) — esse M2M é a fonte de verdade de "em quais países essa
    # agência aparece", incluindo o país da própria sede. id_estado continua
    # só pra endereço/cidade de exibição.
    paises_atendidos = models.ManyToManyField(
        'Pais', related_name='agencias_atendidas', blank=True,
        verbose_name="Países atendidos", help_text="Todos os países onde a agência tem unidade/atuação — inclui o país da sede.",
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='agencia'
    )
    tags = models.ManyToManyField('Tag', related_name='agencias', blank=True)
    layout = models.JSONField(
        default=list, blank=True,
        verbose_name="Layout da página",
        help_text="Lista ordenada de seções e variantes escolhidas pela agência no editor de página (conta business). Vazio = layout padrão.",
    )
    imagem_capa = models.ImageField(
        upload_to='agencias/capas/', blank=True, null=True,
        verbose_name="Imagem de capa",
        help_text="Banner exibido no topo da página quando a variante \"banner cheio\" do hero está selecionada.",
    )
    # Ponto focal da imagem de capa, em % (0-100) a partir do canto
    # superior esquerdo — usado como object-position/background-position
    # pra manter o que importa da foto visível quando a tela corta a
    # imagem (banner bem mais largo que alto, versão mobile, etc).
    imagem_capa_foco_x = models.FloatField(default=50)
    imagem_capa_foco_y = models.FloatField(default=50)
    # Conteúdo em texto livre das seções "simples" do editor de blocos —
    # cada uma guarda seu próprio formato aqui em vez de ganhar uma coluna
    # (ou tabela) só pra si; a validação de formato fica por conta do
    # front, que é quem também lê isso de volta. Chaves possíveis:
    # video ({url}), equipe ({membros:[{nome,cargo}]}),
    # certificacoes ({itens:[{nome,descricao}]}),
    # faq ({perguntas:[{pergunta,resposta}]}),
    # localizacao ({link_mapa}),
    # redes_sociais ({instagram,facebook,tiktok,linkedin,youtube}),
    # contato_whatsapp ({numero,mensagem}).
    conteudo_blocos = models.JSONField(default=dict, blank=True, verbose_name="Conteúdo das seções")

    def __str__(self):
        return f"{self.id} - {self.nome}"

    class Meta:
        verbose_name = "Agencia"
        verbose_name_plural = "Agencias"