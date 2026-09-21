"""Texto do manual. Fonte: Script de Vendas v2.0 e Manual de Procedimento Interno v1.0.

Para atualizar o manual, edite apenas este arquivo. Cada entrada é (título, markdown).
Falas para o cliente ficam em blocos de citação (>).
"""

TESE = "Tese institucional vigente: prescrição 10 anos, parâmetro BACEN + 50%."

SCRIPT = [
    ("Observações gerais", """
Este script é guia, não texto a ser lido. O operador adapta tom e sequência ao perfil do cliente. Três regras valem em qualquer cenário.

**Nunca prometer resultado.** Cada caso depende de análise técnica e da decisão judicial.

**Nunca usar expressões que sugiram pressão indevida sobre o juízo.** O acompanhamento ativo se dá por peticionamento e contato regular com a vara, dentro dos limites éticos da advocacia.

**Registrar o consentimento LGPD por escrito no WhatsApp** logo após a ligação, com a mensagem-padrão do Procedimento Interno (item 1.1).
"""),
    ("1. Abertura e identificação", """
#### 1.1A Abertura padrão (sem aviso de gravação)
:red[Abertura em uso hoje. As ligações comerciais não são gravadas, portanto não há aviso de gravação. O registro LGPD é feito por escrito no WhatsApp, após a ligação.]

> Sr(a). [NOME], boa tarde. Meu nome é [NOME DO OPERADOR], falo do escritório Dutra Bitencourt. O(a) senhor(a) esteve em contato conosco há pouco. Ligo agora para conversarmos com calma sobre demandas bancárias: empréstimos, cartão RMC ou RCC, e cobranças que muitas vezes passam despercebidas no contracheque ou na conta corrente.
>
> Antes de seguir, posso entender melhor a sua situação? Vou fazer algumas perguntas rápidas.

#### 1.1B Abertura alternativa (com aviso de gravação)
:red[Usar somente se o escritório passar a gravar as ligações comerciais. Nesse cenário o aviso é obrigatório e o consentimento LGPD pode ser capturado verbalmente, complementado por confirmação escrita no WhatsApp.]

> Sr(a). [NOME], boa tarde. Antes de iniciar, informo que esta ligação está sendo gravada para registro do nosso atendimento e que os dados que o(a) senhor(a) compartilhar serão tratados exclusivamente para a condução da sua eventual ação, conforme a Lei Geral de Proteção de Dados. O(a) senhor(a) está de acordo em seguirmos?
>
> Meu nome é [NOME DO OPERADOR], falo do escritório Dutra Bitencourt. O(a) senhor(a) esteve em contato conosco há pouco. Ligo agora para conversarmos com calma sobre demandas bancárias: empréstimos, cartão RMC ou RCC, e cobranças que muitas vezes passam despercebidas no contracheque ou na conta corrente.

#### 1.2 Apresentação ao cliente
Após a abertura, o operador contextualiza o escritório e a finalidade da ligação. A apresentação detalhada vai na Parte 3.

#### 1.3 Diagnóstico do caso
Perguntas-âncora, na sequência sugerida:

1. O(a) senhor(a) recorda de contratações bancárias feitas nos últimos anos?
2. Quais bancos? AGIBANK, BMG, CREFISA, FACTA, REALIZE, VIA CREDI, CREFAZ e SIMPALA são os mais comuns. Pode mencionar outros.
3. O contrato já foi quitado, está em pagamento ou em atraso?
4. Os descontos ocorrem no contracheque/benefício ou direto na conta corrente?
5. Há cartão RMC ou RCC? Recebeu o cartão? Desbloqueou? Usou para compras em lojas, mercados, farmácias, ou só para sacar o empréstimo?
6. É aposentado(a), pensionista do INSS, servidor(a) público(a) ou trabalha com CLT/autônomo?
7. Já tentou resolver administrativamente com o banco, ou já falou com outro advogado?

#### 1.4 Validação de viabilidade
A validação é feita ainda na ligação.

| Situação | Conduta |
|---|---|
| Banco envolvido apenas Portocred | Informar que no momento o escritório não aceita casos contra essa instituição. |
| Cliente usou o cartão RMC/RCC para compras | Explicar que o uso costuma ser interpretado como aceite e que, isoladamente, o caso não tem avanço viável. |
| Cliente já não sofre desconto do RMC/RCC | A tese principal perde força e o caso, em regra, não avança só por essa via. |
| Casos só contra Banrisul, Caixa, Santander, Bradesco, Sicoob ou Banco do Brasil | Explicar que esses bancos exigem apresentação prévia de contratos e demonstrativos. |
| Revisão de juros remuneratórios em consignado do INSS (fora RMC/RCC) | Em regra não avança, pois as taxas costumam estar dentro da média de mercado. |

Quando o caso não tem viabilidade, comunicar com transparência:

> Sr(a). [NOME], pelo cenário que o(a) senhor(a) me descreveu, hoje o caso não apresenta os requisitos mínimos que o escritório utiliza para ajuizar a ação com chance real de êxito. Caso surjam novos documentos ou novos descontos, podemos reavaliar.
"""),
    ("2. Problema e solução", """
#### 2.1 Juros abusivos
> Toda instituição financeira é regulada pelo Banco Central. O Banco Central divulga mensalmente a taxa média de juros praticada pelas instituições para cada modalidade de crédito.
>
> O entendimento jurisprudencial predominante considera abusiva a taxa que supera em 50% a média divulgada pelo Banco Central para a modalidade contratada. Em muitos contratos de empréstimo pessoal, a taxa cobrada é várias vezes superior à média de mercado, e o cliente sequer tem consciência disso.
>
> A revisão tem como objetivo levar o contrato ao Judiciário e pedir o recálculo. Se houver abusividade reconhecida, o juiz determina a aplicação de uma taxa adequada e o recálculo das parcelas, com restituição do que foi pago a mais.

As médias do BACEN são consultadas em tempo real no [SGS do Banco Central](https://www3.bcb.gov.br/sgspub/). Valores fixos não entram no script porque variam mensalmente.

#### 2.2 RMC e RCC
> Os cartões RMC e RCC são vendidos como cartões de crédito consignados, mas funcionam de maneira muito diferente. O desconto no contracheque ou no benefício é mensal, em um percentual da remuneração, e é tratado pelo banco como pagamento mínimo da fatura.
>
> O resultado prático é que a dívida não diminui. O cliente paga continuamente, sem prazo final definido, e em muitos casos termina pagando várias vezes o valor que recebeu. Quando o cliente sequer chegou a usar o cartão para compras, a discussão é ainda mais clara: ele queria um empréstimo, recebeu um cartão e segue sendo descontado indefinidamente.
>
> Nessas ações, o pedido principal é a conversão do cartão em empréstimo consignado comum, com parcela fixa e prazo definido, e a restituição dos valores pagos além do que seria devido nessa modalidade.

#### 2.3 Venda casada / seguro
> Em vários contratos, especialmente em consignados do INSS, identificamos a cobrança de seguros ou pacotes de benefícios que o cliente não foi informado, ou que não teve a opção de recusar. Quando isso ocorre, configura-se venda casada, vedada pelo CDC.
>
> Nessa hipótese, o pedido inclui a restituição dos valores cobrados a esse título, observados os parâmetros legais aplicáveis.

#### 2.4 Benefícios da revisão
Restituição dos valores pagos a mais, quando o contrato já foi quitado. Redução do saldo devedor, quando ainda está em pagamento. Readequação das parcelas à taxa fixada em juízo. No RMC/RCC, conversão em empréstimo comum com parcela fixa e prazo determinado. Na venda casada, restituição do que foi cobrado indevidamente. Havendo negativação vinculada à dívida discutida, possibilidade de regularização conforme o resultado da ação.
"""),
    ("3. Diferenciais do escritório", """
#### 3.1 Especialização e atuação nacional
> Atuamos com foco em direito bancário e defesa do consumidor pessoa física, com base em Porto Alegre/RS e atendimento em todo o território nacional. A ação é sempre ajuizada no domicílio do cliente. O atendimento é integralmente remoto, sem necessidade de deslocamento.

#### 3.2 Equipe multidisciplinar
> O caso é conduzido por três frentes integradas. O Núcleo Bancário cuida do levantamento documental, da apuração dos valores e do parecer técnico que orienta a estratégia. O setor jurídico elabora a tese, distribui a ação e acompanha cada movimentação. Na fase de execução, o Núcleo Bancário e Contábil revalida os cálculos para garantir que o valor depositado é o valor correto.
>
> Esse desenho aumenta a precisão da causa de pedir e protege o resultado: muitas ações ganham na sentença e perdem valor na execução por falta de revisão técnica.

#### 3.3 Acompanhamento processual
> O cliente é direcionado a um WhatsApp exclusivo de relacionamento com o advogado responsável pelo caso. Atualizações periódicas são enviadas mesmo quando não há perguntas pendentes, e qualquer dúvida é respondida diretamente pela equipe técnica. O escritório mantém política de acompanhamento ativo, com peticionamento regular e contato com a vara dentro dos limites éticos da advocacia, sempre que isso puder agregar à tramitação.
"""),
    ("4. Política de cobrança", """
#### 4.1 Modelo único de honorários
> A forma de cobrança do escritório, em ações revisionais bancárias, é única e padronizada: 30% sobre o êxito da ação, somados a R$ 500,00, tudo cobrado ao final, descontados diretamente do alvará. Não há cobrança antecipada e não há mensalidade.
>
> Se o caso não gerar resultado econômico para o(a) senhor(a), nada é cobrado. Isso vale para qualquer cenário, independentemente do tempo de tramitação.

O operador não oferece modelos alternativos, percentuais distintos ou condições particulares. A padronização é institucional.

#### 4.2 Não-promessa de resultado
> É importante deixar claro: ninguém pode garantir o resultado da ação, porque a decisão é do Judiciário. O que o escritório pode garantir é a condução técnica adequada, com a documentação correta, a tese aplicável e o acompanhamento até o cumprimento da decisão.

#### 4.3 Janela temporal
> O prazo para discutir esses contratos é de 10 anos, contados da data em que o contrato foi formalizado. Quanto mais tempo se espera para ajuizar a ação, menor o período de parcelas e descontos passível de devolução. Nos contratos de RMC e RCC, por serem de trato sucessivo, a situação tem particularidades, mas a regra geral é simples: quanto antes a revisão for proposta, maior o valor potencialmente recuperado.
"""),
    ("5. Dúvidas e objeções", """
**"O escritório fica longe da minha cidade?"**
> A sede física fica em Porto Alegre, mas a atuação é nacional. A ação é ajuizada no domicílio do(a) senhor(a), portanto fica perto da sua casa. O nosso trabalho com o(a) senhor(a) é todo remoto, por WhatsApp e telefone. Hoje, mais de 95% dos nossos clientes vivem em outros estados.

**"Já quitei o contrato. Ainda dá para revisar?"**
> Sim. Em muitos casos é até melhor, porque a discussão fica exclusivamente sobre o que foi pago a mais. Não há mais risco de cobrança ou negativação envolvida. A revisão recalcula o contrato e apura, sobre os pagamentos efetuados, o valor que deveria ser restituído.

**"Vou negociar direto com o banco. Vale a pena?"**
> A negociação direta normalmente parte da dívida que o banco já calculou, que pode estar inflada justamente pela abusividade. O desconto oferecido pode ser apenas sobre um valor já irregular. Sem a revisão, o(a) senhor(a) negocia sem saber se o número apresentado é correto. A revisão dá clareza sobre o valor justo e, a partir daí, sim, faz sentido negociar.

**"Entrar com ação prejudica a minha relação com o banco?"**
> Em regra, não. A legislação protege o consumidor contra represálias. Em casos específicos, como Banrisul, pode haver restrição a alguns serviços (cartão de crédito, cheque especial, conta corrente). Quando esse for um ponto sensível, conversamos antes de avançar.

**"E se eu usei o cartão RMC/RCC?"**
> Se o cartão foi efetivamente usado para compras em estabelecimentos, isso costuma ser interpretado como aceite da contratação e enfraquece a tese principal. Cada caso é avaliado, mas, na maioria das situações em que o cartão foi utilizado, o escritório não recomenda o ajuizamento.

**"Não tenho documentos. Ainda posso entrar?"**
> Sim, podemos te ajudar a buscar. O escritório orienta o cliente a obter contratos e extratos junto ao banco e também acessa canais como Registrato do Banco Central e o consumidor.gov.br. Sem essa documentação, porém, a análise técnica fica incompleta. A cooperação na fase documental é parte central do trabalho.

**"Faz mais de 5 anos. Ainda posso revisar?"**
> Sim. A tese adotada pelo escritório considera prescrição de 10 anos, contados da formalização do contrato. Portanto, contratos celebrados nos últimos 10 anos seguem revisáveis.
"""),
    ("6. Fechamento", """
#### 6.1 Envio de contrato e procuração
> Sr(a). [NOME], com o seu de acordo, vou te enviar agora dois documentos: o nosso contrato de honorários, que é objetivo e tem apenas uma página, com a política que combinamos (30% sobre o êxito mais R$ 500,00, tudo descontado do alvará ao final), e a procuração judicial, que dá ao escritório poderes específicos para ajuizar essa ação em seu nome.
>
> Você analisa e, se estiver de acordo, assina digitalmente. Envio em seguida um vídeo curto explicando como funciona a assinatura.

#### 6.2 Próximos passos
> Assinado o contrato, o(a) senhor(a) passa para o atendimento do nosso Núcleo Bancário. A equipe vai entrar em contato pelo WhatsApp, pedir a documentação inicial e explicar a primeira etapa com calma. A partir daí, o caso é montado: levantamento documental, apuração dos valores na nossa ferramenta de cálculo, parecer técnico e definição de quantas ações serão ajuizadas. Em seguida, o jurídico distribui e o(a) senhor(a) é apresentado ao advogado responsável.

#### 6.3 Encerramento
> Muito obrigado(a) pelo seu tempo e pela atenção. Já encaminho os documentos. Qualquer dúvida durante a análise, é só me chamar.

#### 6.4 Confirmação da assinatura
Após o envio, aguardar a confirmação da assinatura digital. Assim que o sistema acusar contrato e procuração assinados, seguir imediatamente para a Parte 7. Não encerrar a ligação antes de comunicar ao cliente sobre o contato da equipe técnica.
"""),
    ("7. Após a assinatura", """
:red[Parte obrigatória, executada antes de encerrar a ligação. Sem este aviso, é comum o cliente não responder à equipe técnica (acha que é spam) ou cair em tentativas de fraude de terceiros se passando pelo escritório.]

#### 7.1 Aviso sobre o contato da equipe técnica
> Sr(a). [NOME], a partir daqui o(a) senhor(a) passa para o atendimento da nossa equipe técnica, do Núcleo Bancário. Em até [24 horas úteis / próximo dia útil], o número oficial do escritório vai entrar em contato com o(a) senhor(a) pelo WhatsApp.
>
> É por esse número que vamos te orientar, pedir a documentação inicial e dar o andamento do seu processo. Vou te encaminhar agora o contato salvo do escritório aqui no WhatsApp, para o(a) senhor(a) guardar como Dutra Bitencourt – Núcleo Bancário.

**Ação operacional:** enviar, na mesma conversa do WhatsApp, o cartão de contato do número oficial da equipe técnica. Confirmar que o cliente recebeu e salvou.

#### 7.2 Aviso de segurança
> Por segurança, é importante o(a) senhor(a) saber: somente o número oficial que estou te encaminhando agora é da nossa equipe técnica. Caso receba mensagens ou ligações de outros números pedindo dados pessoais, senhas, pagamentos por Pix ou documentos em nome do escritório, desconsidere e me chame para confirmarmos.
>
> O escritório nunca pede pagamento de honorários por antecipação, nem cobra valor algum antes do final da ação. Tudo o que combinamos está no contrato que o(a) senhor(a) assinou.

#### 7.3 Próximos passos com a equipe técnica
> Assim que a equipe técnica te chamar, ela vai pedir alguns documentos iniciais (RG, comprovante de residência, contracheques, extratos e o que mais for relevante para o seu caso) e te orientar sobre o que precisamos buscar com o banco, caso falte alguma coisa.
>
> A partir daí, o caso é montado: levantamento documental, apuração dos valores na nossa ferramenta de cálculo, parecer técnico e definição de quantas ações serão ajuizadas no seu caso. Em seguida, o jurídico distribui a ação e o(a) senhor(a) é apresentado ao advogado responsável, que passa a te acompanhar por um WhatsApp exclusivo.

#### 7.4 Encerramento da ligação
> Combinado, Sr(a). [NOME]? Muito obrigado(a) pelo seu tempo, pela atenção e pela confiança no escritório. Se aparecer qualquer dúvida nesse intervalo até a nossa equipe técnica te chamar, é só me responder aqui mesmo.
"""),
]

PROCEDIMENTO = [
    ("1. Onboarding", """
#### 1.1 Mensagem inicial no WhatsApp
Após o fechamento comercial e o aceite do contrato, o atendente do Núcleo Bancário abre o WhatsApp com a mensagem abaixo. É também o momento de registrar por escrito o consentimento LGPD, já que as ligações comerciais não são gravadas.

```
Olá, [NOME]! Tudo bem?
Sou [NOME DO ATENDENTE], da equipe Dutra Bitencourt. Vou te acompanhar no andamento da sua ação de revisão bancária.
Neste primeiro contato, gostaria de me apresentar, confirmar alguns dados e te enviar a lista dos documentos que vamos precisar para fortalecer o seu processo. Quando precisarmos buscar documentos junto ao banco, também auxiliamos.
Para seguirmos, preciso confirmar: você autoriza o escritório a tratar seus dados pessoais e bancários exclusivamente para a condução da sua ação, conforme o nosso contrato e a Lei Geral de Proteção de Dados? Pode me responder "autorizo" aqui no WhatsApp para registro.
Posso te ligar para esse primeiro alinhamento? Qual horário fica melhor para você?
```

**Registro do consentimento:** a resposta escrita do cliente ("autorizo" ou equivalente) é o registro válido. Salvar print da conversa na pasta Documentos Pessoais.

#### 1.2 Ligação de boas-vindas
Confirma dados pessoais e endereço, bancos envolvidos, modalidades e descontos atuais. Reforça verbalmente o consentimento LGPD já obtido por escrito. Deixa claro que não há promessa de resultado. Explica o fluxo: documentos, apuração de valores, parecer, minuta, distribuição. Como a ligação não é gravada, toda informação relevante vai por escrito no Relatório do Caso.

#### 1.3 Lista de documentos
Enviada pelo WhatsApp após a ligação e personalizada conforme o produto. Os documentos podem vir pelo próprio WhatsApp ou por e-mail para documentos@dutrabitencourt.com.br.

1. Documento de identificação (RG ou CNH).
2. Comprovante de residência dos últimos 60 dias.
3. Cópia dos contratos discutidos, se o cliente tiver.
4. Extratos bancários do período de desconto (preferencialmente 12 a 60 meses).
5. Contracheque ou extrato de benefício do último mês e dos meses com desconto.
6. Extrato de consignações (servidores e beneficiários do INSS).
7. Comprovantes de pagamento das parcelas, se houver.
8. Faturas do cartão RMC/RCC, quando aplicável.
9. Informe de Rendimentos (o máximo de anos possível, especialmente Agibank).
10. Relatório SCR do Banco Central (últimos 5 anos), quando possível.

#### 1.4 Recebimento da documentação
Criar a pasta do cliente no Drive, colar o link no card do CRM e organizar conforme o item 6. Nomear cada documento com tipo, fonte e mês, por exemplo `EXTRATO BANRISUL JUL-2024`, `FATURA RMC BMG MAR-2025`, `CONTRACHEQUE INSS AGO-2025`. Contracheques e extratos em ordem cronológica. O card só avança com a documentação mínima completa (item 7).
"""),
    ("2. Documentos por produto", """
#### 2.1 Empréstimo pessoal não consignado
Débito em conta, carnê, boleto ou financiamento de veículo. Essenciais: contrato ou demonstrativo de dívida; extratos com os débitos (12 a 60 meses); comprovantes de pagamento, se houver; comprovação do valor recebido (TED, depósito, crédito em conta).

Maior incidência de abusividade: AGIBANK, BMG, CREFISA, FACTA, REALIZE, VIA CREDI, CREFAZ, SIMPALA.
Análise mais cautelosa: BANRISUL, CAIXA, SANTANDER, BRADESCO, SICOOB, BANCO DO BRASIL, em que o cliente busca contrato ou demonstrativo na agência antes do avanço.
:red[Restrição institucional: não são aceitos casos contra a PORTOCRED, em razão da liquidação extrajudicial em curso.]

#### 2.2 Consignado de servidor público
Foco em FACTA e SIMPALA. Essenciais: contrato, contracheque com o desconto, extrato de consignações, comprovantes se aplicável.
Consignados do INSS, ressalvado o RMC/RCC, em regra não têm taxa abusiva. Não criar no cliente expectativa de revisão de juros remuneratórios desses contratos.

#### 2.3 Cartão RMC
Desconto recorrente em folha ou benefício (em torno de 5% da remuneração), sem prazo final, tratado pelo banco como pagamento mínimo da fatura. Essenciais: contracheque com o desconto RMC, extrato de consignações, faturas (preferencialmente várias), comprovação do valor inicialmente recebido, contrato ou proposta de adesão se houver.

**Filtro obrigatório:** perguntar se o cliente recebeu o cartão físico, se desbloqueou e se usou para compras. Uso confirmado costuma ser lido como aceite. Sem desconto atual, a tese principal deixa de existir e o caso, em regra, é descartado.

#### 2.4 Cartão RCC
Mesma lógica, documentação e filtros do RMC.

#### 2.5 Venda casada / seguro
Foco em consignados do INSS com a FACTA, com seguro ou pacote não solicitado. Essenciais: contrato com a cláusula de seguro destacada, contracheque com o desconto do seguro, extrato com débito separado quando for o caso.

**Filtro obrigatório:** perguntar se a cobrança do seguro foi informada e se houve opção de recusar. Sem essa narrativa, a tese fica frágil.
"""),
    ("3. Análise de viabilidade", """
#### 3.1 Filtros objetivos
Duas etapas: qualificação pelo SDR antes do fechamento e revalidação pelo Núcleo Bancário após a documentação. Critérios mínimos: cliente possui ou possuiu contrato com instituição financeira; há descontos atuais (RMC/RCC) ou descontos comprováveis dentro do prazo prescricional adotado; cliente tem ao menos identificação, comprovante de residência e um documento bancário; banco fora da lista de restrição.

#### 3.2 Restrições institucionais
| Hipótese | Regra |
|---|---|
| PORTOCRED | Não avançar (liquidação extrajudicial). |
| Só BANRISUL, CAIXA, SANTANDER, BRADESCO, SICOOB ou BB | Avança apenas com contrato ou demonstrativo prévio. |
| RMC/RCC usado para compras | Descartar como regra, salvo cenário excepcional avaliado pelo jurídico. |
| RMC/RCC sem desconto atual | Descartar como regra. |
| Juros remuneratórios em consignado do INSS | Não avançar, salvo análise jurídica específica. |

#### 3.3 Parâmetros de abusividade e prescrição
**Abusividade:** taxa que supera em 50% a média BACEN da modalidade no mês da contratação. Consulta no [SGS](https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do).

**Prescrição:** tese institucional decenal, contada da formalização do contrato. No RMC e RCC, por serem de trato sucessivo, o foco está nos descontos contínuos e atuais, ainda que o contrato originário seja antigo.

**Sinais de alerta:** parcela muito acima do devido para o valor liberado, considerando a média BACEN do mês; seguro ou pacote sem contratação autônoma; refinanciamentos sucessivos; cartão consignado tratado pelo cliente como empréstimo comum; descontos que em poucos anos somam várias vezes o valor recebido.
"""),
    ("4. Apuração de valores e parecer", """
Etapa conduzida pelo Núcleo Bancário após o fechamento e a documentação completa.

#### 4.1 Ferramenta de cálculo
Apuração exclusivamente na ferramenta interna do escritório: [sistema de cálculos revisionais](https://dutrabitencourt-revisional.streamlit.app/). :red[A credencial de acesso não fica neste manual; solicite à coordenação.]

Usos: pré-ajuizamento (valor pago a mais, saldo devedor recalculado, restituição estimada por contrato) e pós-sentença (valor devido na execução, revalidação e contraposição a cálculos do banco ou do perito).

Entradas: modalidade; data de entabulação (média BACEN do mês e prescrição); valor financiado ou recebido; número e valor das parcelas; taxa aplicada, quando houver no contrato; histórico de pagamentos.

#### 4.2 Quantidade de ações
Regra prática: uma ação por banco, salvo estratégia de agrupamento ou desmembramento justificada no parecer. Vários contratos do mesmo banco e modalidade: em regra uma ação por contrato, salvo exigência do tribunal. Bancos distintos: uma ação por banco. Modalidades distintas no mesmo banco: avaliar agrupamento conforme tese e competência. Refinanciamentos encadeados: cadeia única na mesma ação.

#### 4.3 Parecer Jurídico Interno
Estrutura: identificação dos contratos; modalidade, data, banco, valor e parcelas; comparação da taxa com a média BACEN do mês; valores apurados; tese aplicável; análise da prescrição decenal; quantidade de ações e razão da divisão; riscos (uso do cartão, documento faltante, banco que exige cautela); conclusão (ajuizar, ajuizar com ressalva ou descartar).
"""),
    ("5. Busca de documentos", """
#### 5.1 Ordem de tentativa
1. Aplicativo e portal do banco, com instrução passo a passo pelo WhatsApp.
2. Solicitação na agência, com pedido formal de cópia integral de contratos e demonstrativos.
3. Registrato do Banco Central (SCR e relacionamento com instituições).
4. Mediação: consumidor.gov.br, Reclame Aqui, SAC e ouvidoria.
5. Solicitação direta do escritório ao banco, por e-mail com procuração e documentos do cliente.

#### 5.2 Modelos
**Ao cliente, documentos faltantes**
```
Sr(a). [NOME], analisamos a documentação enviada e identificamos a necessidade de complementar com o(s) seguinte(s) documento(s): [LISTAR].
Esses documentos são fundamentais para fortalecer o seu processo. Vou te orientar como obter cada um deles.
[Caminho no aplicativo do banco / visita à agência / acesso ao Registrato]
```

**Ao banco, contratos e demonstrativos**
```
Prezados, boa tarde.
Falo do escritório Dutra Bitencourt Advocacia e representamos o(a) Sr(a). [NOME DO CLIENTE], inscrito(a) no CPF [000.000.000-00], em ação revisional de contratos bancários.
Solicito a remessa de cópia integral dos contratos firmados entre o(a) cliente e essa instituição, bem como dos respectivos demonstrativos de dívida, extratos e eventuais documentos vinculados, especialmente os relativos ao(s) contrato(s) [NÚMERO/IDENTIFICAÇÃO, SE DISPONÍVEL].
Seguem em anexo a procuração assinada pelo(a) cliente, o documento de identificação e a inscrição na OAB do procurador.
Ficamos à disposição por este e-mail e pelo telefone (51) 98035-3503.
Atenciosamente,
```
Sempre anexar procuração, identificação do cliente e OAB do advogado. Se o banco tiver formulário próprio, encaminhar para assinatura do advogado responsável.
"""),
    ("6. Organização no Drive", """
| Pasta | Conteúdo |
|---|---|
| 1 – Documentos Pessoais | Identificação, comprovante de residência, contrato de honorários, procuração, print do consentimento LGPD. |
| 2 – Documentos Contratuais e Bancários | Contratos, faturas RMC/RCC, boletos, demonstrativos, Relatório SCR. Subpasta por banco quando houver mais de um. |
| 3 – Documentos de Renda e Descontos | Contracheques, extratos, extrato de consignações, informe de rendimentos, demais comprovantes de desconto. |

Na raiz da pasta ficam o Relatório do Caso e o Parecer Jurídico Interno, copiados dos modelos institucionais, com links no card. Não editar os modelos originais. Cada documento é nomeado com tipo, fonte e mês.
"""),
    ("7. Checklist", """
Antes de encaminhar para a apuração de valores, conferir:

- [ ] Card do CRM totalmente preenchido
- [ ] Pastas 1, 2 e 3 criadas e organizadas
- [ ] Relatório do Caso preenchido
- [ ] Documentação mínima do produto reunida
- [ ] Filtros de viabilidade revalidados após a análise documental
- [ ] Consentimento LGPD registrado por escrito (print na pasta 1)
- [ ] Contrato de honorários e procuração assinados

Mensagem ao cliente após o checklist:
```
Sr(a). [NOME], com a documentação completa, nosso Núcleo Bancário vai apurar agora os valores e definir a estratégia da ação. Em seguida, confeccionamos a minuta e distribuímos. Assim que o processo for distribuído, retornamos com o número e os próximos passos.
```
"""),
    ("8. Encaminhamento e acompanhamento", """
**Núcleo Bancário:** apuração e parecer (item 4), com restituição estimada, saldo recalculado, quantidade e identificação das ações.

**Jurídico:** recebe o parecer, elabora as minutas e distribui no domicílio do cliente. O atendimento migra para o WhatsApp exclusivo do advogado responsável.

**Acompanhamento:** atualizações periódicas ao cliente e acompanhamento ativo, com peticionamento e contato regular com a vara, dentro dos limites éticos da advocacia.
"""),
    ("9. Execução, alvará e repasse", """
Com a sentença e esgotados os recursos, o processo vai à execução. O Núcleo Bancário usa novamente a ferramenta de cálculo para apurar o valor devido e revalidar os cálculos, inclusive contra perícia ou cálculo do banco.

Depositado o valor, é expedido alvará em favor do escritório. O financeiro confere o depósito, aplica os honorários contratados (30% sobre o êxito mais R$ 500,00, descontados do alvará) e repassa o líquido ao cliente após conferir os dados bancários.

Nas obrigações de fazer (cancelamento ou readequação de parcela), o escritório acompanha o cumprimento até a efetiva implementação.
"""),
]
