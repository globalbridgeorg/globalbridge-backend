# Configuração de e-mail em produção

## Diagnóstico

Os e-mails do site (boas-vindas, código de login, redefinição de senha, status
de pedido de agência) não chegam no Gmail por dois motivos, os dois em
produção (Railway):

1. **Nenhuma variável de e-mail está configurada** no serviço
   `globalbridge-backend` no Railway (`BREVO_API_KEY` / `EMAIL_HOST` ausentes).
   Sem isso, o Django cai no backend de "console" — o e-mail só é impresso no
   log do servidor, nunca é enviado de verdade (ver `EMAIL_BACKEND` em
   `app/settings.py`).
2. O remetente já cadastrado no Brevo (`globalbridgecontato@gmail.com`) é um
   endereço `@gmail.com` — um domínio "freemail" que não pode ser autenticado
   com DKIM/DMARC (só o Google controla o DNS de `gmail.com`). Desde 2024 o
   Google exige SPF+DKIM+DMARC alinhados para remetentes em volume; um
   remetente `@gmail.com` enviado por infraestrutura de terceiros (Brevo)
   falha essa checagem por definição, então o próprio Gmail rejeita ou joga
   pro spam.

Falhas de envio hoje já são tratadas com segurança pelo código (try/except +
log em `core/serializers/user.py`, `core/serializers/solicitacao_agencia.py`
e `core/admin.py`) — o site nunca quebra por causa disso, mas também ninguém
percebe que o e-mail não saiu a não ser olhando o log do Railway.

## O que precisa ser feito

### 1. Registrar um domínio próprio

Precisa ser um domínio que a GlobalBridge controle (não pode ser
`@gmail.com`, `@hotmail.com` etc). Sugestão: `globalbridge.com.br` — já é o
domínio citado no texto dos e-mails (`core/emails.py`), mesmo o site ainda
não estando hospedado nele.

- `.com.br`: [registro.br](https://registro.br) (~R$40/ano, precisa de CPF/CNPJ)
- `.com` (mais barato/rápido): Cloudflare, Namecheap, Hostinger

Não precisa hospedar nada nesse domínio — ele pode servir só para o e-mail.

### 2. Verificar o domínio no Brevo

Brevo → **Remetentes, Domínios e Dedicated IPs** → aba **Domínios** →
**Add a domain** → informar o domínio registrado. O Brevo vai gerar
registros DNS (SPF, DKIM, e às vezes um CNAME) para adicionar no painel do
registrador do domínio. Propagação leva de minutos a algumas horas; o Brevo
confirma a verificação automaticamente depois disso.

### 3. Criar o remetente com o domínio verificado

Aba **Remetentes** → adicionar algo como
`GlobalBridge <no-reply@globalbridge.com.br>`. Como o domínio já está
verificado, esse remetente não deve ter mais o aviso de "Freemail" nem de
DKIM.

O remetente antigo (`globalbridgecontato@gmail.com`) pode ser removido do
Brevo depois que o novo estiver funcionando.

### 4. Gerar a API key do Brevo

Brevo → **SMTP & API** → aba **API Keys** → **Generate a new API key**.
Copiar o valor imediatamente (só é mostrado uma vez).

### 5. Configurar as variáveis no Railway

No serviço `globalbridge-backend` → **Variables** → **Raw Editor** → colar:

```
BREVO_API_KEY=<chave gerada no passo 4>
DEFAULT_FROM_EMAIL=GlobalBridge <no-reply@globalbridge.com.br>
FRONTEND_URL=<URL de produção do frontend>
```

- `BREVO_API_KEY` ativa o envio de verdade via Brevo (`core/email_backends.py`).
- `DEFAULT_FROM_EMAIL` precisa bater exatamente com o remetente verificado no
  passo 3, senão o Brevo rejeita o envio.
- `FRONTEND_URL` hoje também está ausente e cai no padrão
  `http://localhost:5173` (`app/settings.py`) — sem configurar, os links
  dentro dos e-mails (redefinir senha, aprovação de agência, etc.) apontariam
  para localhost mesmo em produção. Usar a URL pública real do frontend
  (ex.: a URL do Railway/Vercel ou o domínio final do site).

Depois de salvar, o Railway costuma reiniciar o serviço sozinho. Se não
reiniciar, forçar um redeploy manual na aba **Deployments**.

## Checklist

- [ ] Domínio próprio registrado
- [ ] Domínio verificado na aba "Domínios" do Brevo (SPF/DKIM configurados)
- [ ] Remetente com esse domínio criado e verificado na aba "Remetentes"
- [ ] API key do Brevo gerada
- [ ] `BREVO_API_KEY` configurada no Railway
- [ ] `DEFAULT_FROM_EMAIL` configurada no Railway com o remetente do domínio próprio
- [ ] `FRONTEND_URL` configurada no Railway com a URL pública do frontend
- [ ] Testado: criar uma conta nova (ou pedir redefinição de senha) e confirmar
      que o e-mail chega numa conta Gmail de teste
